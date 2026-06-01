#!/usr/bin/env python3
"""Paper 2 public-feed feasibility probe.

Determines whether real public feeds (NVD/EPSS/KEV) yield enough distinct
positive CVEs (after CPE/catalog matching) to make calibrated vulnerability-host
prioritization meaningful. This is a FEASIBILITY GATE, not an experiment and not
a calibrated result.

Safety:
  - Read-only w.r.t. Paper 1 frozen outputs (results/primary_full_v1/). Writes only
    under the --out dir (paper2/feasibility/...), data/snapshots/, data/cache/.
  - PoC/ExploitDB is OFF by default; --include-poc requires PAPER1_ENABLE_POC_FETCH=true.
  - Never fabricates data. If fetching is blocked (e.g., no network) and no cache
    exists, it reports a clear blocker and exits non-zero (no fake success).
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

import paper1.feeds.epss_client as epss_client
import paper1.feeds.kev_client as kev_client
import paper1.feeds.nvd_client as nvd_client
import paper1.feeds.poc_client as poc_client
from paper1.audit.schema import ExploitSignal, Vulnerability
from paper1.feeds.cve_client import parse_cpe23
from paper1.feeds.poc_client import POC_ENV_FLAG, PoCLicenseGateError
from paper1.model.features import FEATURE_COLUMNS, build_feature_frame
from paper1.model.frames import pairs_to_frame
from paper1.model.labels import label_a
from paper1.model.linear_model import (
    fit_weights_linear,
    fit_weights_logit,
    save_calibration_result,
)
from paper1.model.pairs import build_pairs, product_keys_from_vulnerability
from paper1.synthetic.catalogs import (
    load_host_type_defaults,
    load_product_catalog,
    load_service_catalog,
)
from paper1.synthetic.criticality import compute_criticality
from paper1.synthetic.exposure import compute_exposure
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.synthetic.remediation_complexity import compute_complexity
from paper1.utils.io import atomic_write_json
from paper1.utils.seeds import derive_subseed, make_rng
from paper1.utils.time import parse_date

# NVD CVE 2.0 API caps pubStartDate/pubEndDate ranges at 120 days per request.
_NVD_MAX_RANGE_DAYS = 120

_CACHE_DIR = Path("data/cache/paper2_probe")
_VULN_FIELDS = (
    "cve_id",
    "cwe_ids",
    "cpe_matches",
    "cvss_v4_vector",
    "cvss_v4_base",
    "cvss_v31_vector",
    "cvss_v31_base",
    "cvss_version_used",
    "disclosure_date",
    "vendor_advisory_refs",
    "mitigations_listed",
    "preconditions",
)


class ProbeBlocked(RuntimeError):
    """Raised when required data cannot be obtained (e.g., no network + no cache)."""


# ---------------------------------------------------------------------------
# data acquisition (cache-aware; monkeypatchable feed entrypoints)
# ---------------------------------------------------------------------------


def _cache_path(name: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / name


def _nvd_chunks(start: date, end: date, max_days: int = _NVD_MAX_RANGE_DAYS):
    """Split [start, end] into <=max_days windows (NVD's per-request cap)."""
    cur = start
    while cur <= end:
        chunk_end = min(end, cur + timedelta(days=max_days - 1))
        yield cur, chunk_end
        cur = chunk_end + timedelta(days=1)


def _rec_cve_id(rec: dict) -> str | None:
    cve = rec.get("cve") if isinstance(rec, dict) else None
    if isinstance(cve, dict) and cve.get("id"):
        return cve["id"]
    return rec.get("cve_id") if isinstance(rec, dict) else None


def _dedup_by_cve(records: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for rec in records:
        rid = _rec_cve_id(rec)
        if rid is not None:
            if rid in seen:
                continue
            seen.add(rid)
        out.append(rec)
    return out


def _chunk_cache_path(cs: date, ce: date) -> Path:
    return _cache_path(f"nvd_chunk_{cs.isoformat()}_{ce.isoformat()}.json")


def _resume_command(start: date, end: date) -> str:
    """Exact command to resume a partial NVD acquisition (per-chunk caches kept)."""
    return (
        "NVD_API_KEY=<your_key> .venv/bin/python scripts/paper2_feasibility_probe.py "
        f"--resume --start-date {start.isoformat()} --end-date {end.isoformat()} "
        "  # add --multi-t0 and the same t0/lookback flags for a multi-t0 run"
    )


def _obtain_nvd(
    start: date,
    end: date,
    *,
    skip_fetch: bool,
    cached_only: bool,
    api_key: str | None = None,
    sleep_seconds: float = 1.0,
    resume: bool = False,
    status: dict[str, Any] | None = None,
) -> list[dict]:
    """Acquire the NVD universe in <=120-day chunks with per-chunk caching.

    Hardened for Step 3.6:
      - Each <=120-day chunk is cached at ``nvd_chunk_{cs}_{ce}.json`` so a fetch
        interrupted by HTTP 429 can be resumed without re-fetching prior chunks.
      - ``api_key`` (from ``NVD_API_KEY``) is forwarded to the NVD client; pacing
        between chunks is configurable via ``sleep_seconds``.
      - On any fetch error the completed chunks are preserved on disk, a clear
        blocked ``status`` (with a resume command) is recorded, and ``ProbeBlocked``
        is raised — never a fabricated result.
    """
    whole_cache = _cache_path(f"nvd_{start.isoformat()}_{end.isoformat()}.json")
    chunks = list(_nvd_chunks(start, end))

    # cached/offline path: prefer the whole-window cache, else assemble per-chunk caches.
    if skip_fetch or cached_only:
        if whole_cache.exists():
            recs = json.loads(whole_cache.read_text(encoding="utf-8"))
            if status is not None:
                status.update({"source": "whole_window_cache", "total_records": len(recs),
                               "total_chunks": len(chunks), "completed_chunks": len(chunks),
                               "api_key_present": bool(api_key), "blocked": False})
            return recs
        if all(_chunk_cache_path(cs, ce).exists() for cs, ce in chunks):
            recs = []
            for cs, ce in chunks:
                recs.extend(json.loads(_chunk_cache_path(cs, ce).read_text(encoding="utf-8")))
            recs = _dedup_by_cve(recs)
            if status is not None:
                status.update({"source": "per_chunk_cache", "total_records": len(recs),
                               "total_chunks": len(chunks), "completed_chunks": len(chunks),
                               "api_key_present": bool(api_key), "blocked": False})
            return recs
        if status is not None:
            status.update({
                "api_key_present": bool(api_key), "blocked": True, "source": "none_cached",
                "requested_window": [start.isoformat(), end.isoformat()],
                "total_chunks": len(chunks), "completed_chunks": 0,
                "resume_command": _resume_command(start, end),
                "remediation": ("set NVD_API_KEY and re-run without --use-cached-only to "
                                "fetch the full multi-year disclosure universe in "
                                f"{len(chunks)} paced <=120-day chunks"),
            })
        raise ProbeBlocked(
            f"no NVD cache at {whole_cache} (and no complete per-chunk cache for "
            f"{len(chunks)} chunks) and fetching disabled — NVD_API_KEY required for "
            "full-window feasibility (set it and re-run without --use-cached-only)"
        )

    # fetch path: chunked, per-chunk cached, resumable, paced.
    records: list[dict] = []
    chunk_status: list[dict[str, Any]] = []
    fetched_chunks = 0
    for i, (cs, ce) in enumerate(chunks):
        ccache = _chunk_cache_path(cs, ce)
        if ccache.exists() and resume:
            chunk_recs = json.loads(ccache.read_text(encoding="utf-8"))
            chunk_status.append({"window": [cs.isoformat(), ce.isoformat()],
                                 "status": "cached", "records": len(chunk_recs)})
        else:
            try:
                chunk_recs = list(nvd_client.fetch_nvd_window(cs, ce, api_key=api_key))
            except Exception as exc:  # network / HTTP 429 rate-limit / other
                chunk_status.append({"window": [cs.isoformat(), ce.isoformat()],
                                     "status": "failed", "error": str(exc)})
                if status is not None:
                    status.update({
                        "api_key_present": bool(api_key),
                        "requested_window": [start.isoformat(), end.isoformat()],
                        "total_chunks": len(chunks), "completed_chunks": fetched_chunks,
                        "chunks": chunk_status, "blocked": True,
                        "resume_command": _resume_command(start, end),
                    })
                raise ProbeBlocked(
                    f"NVD fetch failed on chunk {cs}..{ce} "
                    f"(api_key_present={bool(api_key)}; unauthenticated NVD is rate-limited "
                    f"with HTTP 429 — set NVD_API_KEY). {fetched_chunks}/{len(chunks)} chunks "
                    f"already cached for --resume: {exc}"
                ) from exc
            ccache.write_text(json.dumps(chunk_recs), encoding="utf-8")
            chunk_status.append({"window": [cs.isoformat(), ce.isoformat()],
                                 "status": "fetched", "records": len(chunk_recs)})
            if i + 1 < len(chunks):  # polite pause between NVD requests
                time.sleep(max(0.0, float(sleep_seconds)))
        fetched_chunks += 1
        records.extend(chunk_recs)

    records = _dedup_by_cve(records)
    whole_cache.write_text(json.dumps(records), encoding="utf-8")
    if status is not None:
        status.update({
            "source": "fetched", "api_key_present": bool(api_key),
            "requested_window": [start.isoformat(), end.isoformat()],
            "total_chunks": len(chunks), "completed_chunks": fetched_chunks,
            "chunks": chunk_status, "total_records": len(records), "blocked": False,
        })
    return records


def _obtain_kev(*, skip_fetch: bool, cached_only: bool) -> dict:
    cache = _cache_path("kev.json")
    if cache.exists() and (skip_fetch or cached_only):
        return json.loads(cache.read_text(encoding="utf-8"))
    if skip_fetch or cached_only:
        raise ProbeBlocked(f"no KEV cache at {cache} and fetching disabled")
    try:
        raw = kev_client.fetch_kev_catalog()
    except Exception as exc:
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        raise ProbeBlocked(f"KEV fetch failed and no cache: {exc}") from exc
    cache.write_text(json.dumps(raw), encoding="utf-8")
    return raw


def _obtain_epss_text(d: date, *, skip_fetch: bool, cached_only: bool) -> str:
    cache = _cache_path(f"epss_{d.isoformat()}.csv")
    if cache.exists() and (skip_fetch or cached_only):
        return cache.read_text(encoding="utf-8")
    if skip_fetch or cached_only:
        raise ProbeBlocked(f"no EPSS cache at {cache} and fetching disabled")
    try:
        raw = epss_client.fetch_epss_csv(d)
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    except Exception as exc:
        if cache.exists():
            return cache.read_text(encoding="utf-8")
        raise ProbeBlocked(f"EPSS fetch failed for {d} and no cache: {exc}") from exc
    cache.write_text(text, encoding="utf-8")
    return text


def _obtain_poc_text(*, include_poc: bool) -> str | None:
    if not include_poc:
        return None
    if os.environ.get(POC_ENV_FLAG, "").lower() != "true":
        raise PoCLicenseGateError(
            f"--include-poc requires {POC_ENV_FLAG}=true (ExploitDB redistribution "
            "is license-gated; PoC data must not be redistributed)."
        )
    cache = _cache_path("poc.csv")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    raw = poc_client.fetch_poc_index()
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    cache.write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------------------


def _catalog_keys() -> set[tuple[str, str]]:
    pc = load_product_catalog()
    return {
        (p["vendor"].lower(), p["product"].lower()) for p in pc.get("products", [])
    }


def _vulns_from_nvd(records: list[dict]) -> tuple[list[Vulnerability], dict[str, int]]:
    counts = {"total_nvd_records": len(records), "normalized_cves": 0, "cves_with_cpe": 0}
    fetched_at = datetime.now(UTC)
    vulns: list[Vulnerability] = []
    for rec in records:
        row, _warns = nvd_client.normalize_nvd_record(rec)
        if row is None:
            continue
        counts["normalized_cves"] += 1
        if not row.get("cpe_matches"):
            continue
        counts["cves_with_cpe"] += 1
        if row.get("cvss_version_used") not in ("v4", "v31"):
            continue
        kwargs = {k: row[k] for k in _VULN_FIELDS if k in row}
        kwargs["feed_fetch_timestamp"] = fetched_at
        try:
            vulns.append(Vulnerability(**kwargs))
        except Exception:  # schema rejection (e.g., bad CWE) — skip, count stands
            continue
    return vulns, counts


def _matches_catalog(vuln: Vulnerability, catalog_keys: set[tuple[str, str]]) -> bool:
    return bool(set(product_keys_from_vulnerability(vuln)) & catalog_keys)


def _t0_dt(t0: date) -> datetime:
    return datetime(t0.year, t0.month, t0.day, tzinfo=UTC)


def _label_bool(v: Any) -> bool | None:
    """Coerce a (possibly nullable/numpy) label value to True/False/None.

    ``label_a`` returns a pandas nullable-boolean Series; iterating yields
    numpy.bool_ or pd.NA, so identity checks (``is True``) are unreliable.
    """
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return bool(v)


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = parse_date(args.t0)
    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    h = int(args.h_days)
    horizon_end = t0 + timedelta(days=h)
    # Labels need observation through t0+H; KEV/NVD are cumulative so use the later
    # of end-date and the horizon as the label-observation window end.
    label_window_end = max(end, horizon_end)

    skip_fetch = bool(args.skip_fetch)
    cached_only = bool(args.use_cached_only)

    # --- acquire data ---
    nvd_records = _obtain_nvd(start, end, skip_fetch=skip_fetch, cached_only=cached_only)
    kev_raw = _obtain_kev(skip_fetch=skip_fetch, cached_only=cached_only)
    epss_text_t0 = _obtain_epss_text(t0, skip_fetch=skip_fetch, cached_only=cached_only)
    poc_text = _obtain_poc_text(include_poc=bool(args.include_poc))

    # --- normalize ---
    vulns_all, nvd_counts = _vulns_from_nvd(nvd_records)
    catalog_keys = _catalog_keys()
    vulns_matched = [v for v in vulns_all if _matches_catalog(v, catalog_keys)]
    # pairs only consider disclosure <= t0 (build_pairs enforces this too)
    vulns_for_pairs = [v for v in vulns_matched if v.disclosure_date <= t0]

    kev_t0 = kev_client.normalize_kev_catalog(kev_raw, as_of_date=t0)
    kev_label = kev_client.normalize_kev_catalog(kev_raw, as_of_date=label_window_end)
    epss_t0 = epss_client.normalize_epss_csv(epss_text_t0, t0)
    poc_label = None
    if poc_text is not None:
        poc_label = poc_client.normalize_exploitdb_csv(poc_text, as_of_date=label_window_end)

    # --- fleet + pairs ---
    hosts = FleetGenerator(
        fleet_size=int(args.fleet_size), seed=int(args.seed), t0=t0
    ).generate()
    pairs = build_pairs(vulns_for_pairs, hosts, t0)
    pair_frame = pairs_to_frame(pairs)
    paired_cves = sorted({p.cve_id for p in pairs})

    # --- labels (Label A over (t0, t0+H]) ---
    labels = label_a(pairs, kev_label, poc_label, t0, h, label_window_end)
    bools = [_label_bool(v) for v in list(labels)]
    pos_pairs = sum(1 for b in bools if b is True)
    neg_pairs = sum(1 for b in bools if b is False)
    pos_cves = sorted(
        {p.cve_id for p, b in zip(pairs, bools, strict=True) if b is True}
    )
    neg_cves = sorted(set(paired_cves) - set(pos_cves))

    # --- KEV counts ---
    kev_t0_cves = set(kev_t0["cve_id"]) if not kev_t0.empty else set()
    kev_label_in_window = 0
    if not kev_label.empty:
        for _, r in kev_label.iterrows():
            d = r["kev_date_added"]
            dd = d if isinstance(d, date) else parse_date(str(d)[:10])
            if t0 < dd <= horizon_end and r["cve_id"] in set(paired_cves):
                kev_label_in_window += 1

    # --- EPSS coverage (t0 + sample prior days) ---
    epss_rows = []
    for k in range(max(1, int(args.epss_sample_days))):
        d = t0 - timedelta(days=k)
        try:
            text = _obtain_epss_text(d, skip_fetch=skip_fetch, cached_only=cached_only)
            frame = epss_client.normalize_epss_csv(text, d)
            present = len(set(frame["cve_id"]) & set(paired_cves)) if paired_cves else 0
            cov = present / len(paired_cves) if paired_cves else 0.0
        except ProbeBlocked:
            present, cov = 0, float("nan")
        epss_rows.append({"date": d.isoformat(), "paired_cves": len(paired_cves),
                          "epss_present": present, "coverage": cov})

    counts = {
        **nvd_counts,
        "catalog_matched_cves": len(vulns_matched),
        "cves_for_pairs_disclosed_le_t0": len(vulns_for_pairs),
        "hosts_generated": len(hosts),
        "pairs_built": len(pairs),
        "distinct_cves_in_pairs": len(paired_cves),
        "label_a_positive_cves": len(pos_cves),
        "label_a_negative_cves": len(neg_cves),
        "positive_pairs": pos_pairs,
        "negative_pairs": neg_pairs,
        "kev_asof_t0_count": len(kev_t0_cves),
        "kev_future_label_count": kev_label_in_window,
        "epss_t0_rows": len(epss_t0),
    }

    # --- calibration attempt (only if gate passes) ---
    calib = _attempt_calibration(
        pairs=pairs,
        pair_frame=pair_frame,
        vulns_for_pairs=vulns_for_pairs,
        hosts=hosts,
        epss_t0=epss_t0,
        kev_t0=kev_t0,
        labels=labels,
        pos_cves=pos_cves,
        neg_cves=neg_cves,
        t0=t0,
        seed=int(args.seed),
        min_positive=int(args.min_positive_cves),
        out=out,
    )

    # --- write outputs ---
    pd.DataFrame(
        [
            {"stage": k, "count": v}
            for k, v in counts.items()
            if k.endswith("cves") or k in ("total_nvd_records", "cves_with_cpe", "catalog_matched_cves")
        ]
    ).to_csv(out / "cve_match_counts.csv", index=False)
    pd.DataFrame(
        [
            {"label": "positive_cves", "count": len(pos_cves)},
            {"label": "negative_cves", "count": len(neg_cves)},
            {"label": "positive_pairs", "count": pos_pairs},
            {"label": "negative_pairs", "count": neg_pairs},
            {"label": "kev_future_label_count", "count": kev_label_in_window},
        ]
    ).to_csv(out / "label_counts.csv", index=False)
    pd.DataFrame(epss_rows).to_csv(out / "epss_coverage.csv", index=False)
    atomic_write_json(out / "calibration_status.json", calib)

    summary = {
        "params": {
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "t0": t0.isoformat(), "h_days": h, "horizon_end": horizon_end.isoformat(),
            "label_window_end": label_window_end.isoformat(),
            "fleet_size": int(args.fleet_size), "seed": int(args.seed),
            "min_positive_cves": int(args.min_positive_cves),
            "include_poc": bool(args.include_poc), "use_cached_only": cached_only,
            "skip_fetch": skip_fetch,
        },
        "counts": counts,
        "calibration": calib,
        "decision": _decide(counts["label_a_positive_cves"], calib),
        "note": (
            "Feasibility probe only; NOT a calibrated result, NOT a paper claim. "
            "Synthetic fleet + public feeds; PoC license-gated and off by default. "
            "Paper 1 frozen outputs untouched."
        ),
    }
    atomic_write_json(out / "summary.json", summary)
    _write_summary_md(out / "summary.md", summary)
    return summary


def _attempt_calibration(
    *, pairs, pair_frame, vulns_for_pairs, hosts, epss_t0, kev_t0, labels,
    pos_cves, neg_cves, t0, seed, min_positive, out,
) -> dict[str, Any]:
    if len(pos_cves) < min_positive:
        return {"attempted": False, "reason": f"positive distinct CVEs {len(pos_cves)} < min {min_positive}"}
    if not neg_cves:
        return {"attempted": False, "reason": "no negative CVEs (single class)"}
    if len(pairs) < 4:
        return {"attempted": False, "reason": f"too few pairs ({len(pairs)})"}

    # Build features (real E/K/S + synthetic C/X/R/U), then dedup to CVE level.
    try:
        feature_frame = _build_features(pairs, pair_frame, vulns_for_pairs, hosts, epss_t0, kev_t0, t0, seed)
    except Exception as exc:
        return {"attempted": False, "reason": f"feature build failed: {exc}"}

    lab_by_pair = {}
    for p, v in zip(pairs, list(labels), strict=True):
        b = _label_bool(v)
        if b is not None:
            lab_by_pair[p.pair_id] = b
    ff = feature_frame.copy()
    ff["label"] = ff["pair_id"].map(lab_by_pair)
    ff = ff.dropna(subset=["label"]).drop_duplicates(subset=["cve_id"]).reset_index(drop=True)
    if ff["label"].nunique() < 2 or len(ff) < 4:
        return {"attempted": False, "reason": "CVE-level frame has <2 classes or <4 rows"}

    y = pd.Series(ff["label"].astype(bool).to_numpy(), dtype="boolean")
    times = [t0] * len(ff)
    # Deterministic ~70/30 split by CVE (feasibility only; real Paper 2 uses temporal splits).
    rng = make_rng(derive_subseed(seed, "probe|split"))
    split = pd.Series(["train" if rng.random() < 0.7 else "test" for _ in range(len(ff))])
    if (split == "train").sum() < 2 or y[split.to_numpy() == "train"].nunique() < 2:
        # ensure train has both classes if possible
        split = pd.Series(["train"] * len(ff))

    result: dict[str, Any] = {"attempted": True, "n_cves": len(ff),
                              "positives": int(y.sum()), "reason": "gate passed"}
    result.update(_run_fits(ff, y, times, split, seed, out))
    return result


def _run_fits(ff, y, times, split, seed, out) -> dict[str, Any]:
    """Fit logistic + ridge weights and record non-degeneracy (no perf claims)."""
    res: dict[str, Any] = {}
    try:
        logit = fit_weights_logit(ff, y, times, split, seed=seed)
        save_calibration_result(logit, out / "calib_logit.json")
        wl = list(logit.weights.values())
        res["logit_weights"] = logit.weights
        res["logit_non_degenerate"] = bool(len({round(w, 9) for w in wl}) > 1)
    except Exception as exc:
        res["logit_error"] = str(exc)
        res["logit_non_degenerate"] = False
    try:
        ridge = fit_weights_linear(ff, y, times, split, seed=seed)
        save_calibration_result(ridge, out / "calib_ridge.json")
        wr = list(ridge.weights.values())
        res["ridge_non_degenerate"] = bool(len({round(w, 9) for w in wr}) > 1)
    except Exception as exc:
        res["ridge_error"] = str(exc)
        res["ridge_non_degenerate"] = False
    res["non_degenerate"] = bool(
        res.get("logit_non_degenerate") or res.get("ridge_non_degenerate")
    )
    return res


def _build_features(pairs, pair_frame, vulns_for_pairs, hosts, epss_t0, kev_t0, t0, seed):
    host_by_id = {h.host_id: h for h in hosts}
    vuln_by_cve = {v.cve_id: v for v in vulns_for_pairs}
    defaults = load_host_type_defaults()
    services = load_service_catalog()
    product_by_key = {
        (p["vendor"].lower(), p["product"].lower()): p
        for p in load_product_catalog()["products"]
    }
    t0_dt = _t0_dt(t0)
    epss_by_cve = dict(zip(epss_t0["cve_id"], epss_t0["epss_score"], strict=False)) if not epss_t0.empty else {}
    epss_pct = dict(zip(epss_t0["cve_id"], epss_t0["epss_percentile"], strict=False)) if not epss_t0.empty else {}
    kev_added = {}
    if not kev_t0.empty:
        for _, r in kev_t0.iterrows():
            d = r["kev_date_added"]
            kev_added[r["cve_id"]] = d if isinstance(d, date) else parse_date(str(d)[:10])

    crit = [
        compute_criticality(host=host_by_id[hid], host_defaults=defaults,
                            identity_config="ad_entra_default", cmdb_staleness_rate=0.0,
                            rng=make_rng(derive_subseed(seed, f"crit|{hid}")), computed_at=t0_dt)
        for hid in sorted({p.host_id for p in pairs})
    ]
    exposures, complexities = [], []
    for p in pairs:
        vuln = vuln_by_cve[p.cve_id]
        parsed = parse_cpe23(vuln.cpe_matches[0])
        pk = (parsed.vendor.lower(), parsed.product.lower())
        meta = product_by_key.get(pk)
        exposures.append(compute_exposure(vulnerability=vuln, host=host_by_id[p.host_id],
                         product_meta=meta, product_key=pk, service_catalog=services,
                         rng=make_rng(derive_subseed(seed, f"expo|{p.pair_id}"))))
        complexities.append(compute_complexity(vuln, host_by_id[p.host_id], meta,
                            make_rng(derive_subseed(seed, f"cmplx|{p.pair_id}"))))
    signals = []
    for cve in sorted({p.cve_id for p in pairs}):
        added = kev_added.get(cve)
        signals.append(ExploitSignal(
            cve_id=cve, epss_score=float(epss_by_cve.get(cve, 0.0)),
            epss_percentile=float(epss_pct.get(cve, 0.5)), epss_fetch_timestamp=t0_dt,
            epss_version="probe", kev_status=cve in kev_added,
            kev_date_added=added if added and added <= t0 else None,
            poc_observed=False, signal_staleness_days=0,
        ))
    ff = build_feature_frame(pair_frame, vulns_for_pairs, signals, crit, exposures, complexities, t0)
    return ff[["pair_id", "cve_id", *FEATURE_COLUMNS]]


def _decide(pos_cves: int, calib: dict) -> str:
    if pos_cves >= 50 and calib.get("non_degenerate"):
        return "GO"
    if 20 <= pos_cves < 50:
        return "CONDITIONAL_GO_expand_window_or_catalog"
    if pos_cves < 20:
        return "PIVOT_away_from_calibration"
    return "REVIEW"


# ---------------------------------------------------------------------------
# multi-t0 feasibility mode (aggregate distinct positive CVEs across t0 windows)
# ---------------------------------------------------------------------------


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _iter_t0s(start: date, end: date, frequency: str) -> list[date]:
    if frequency != "monthly":
        raise ValueError(f"unsupported t0 frequency: {frequency!r} (only 'monthly')")
    out: list[date] = []
    i = 0
    cur = start
    while cur <= end:
        out.append(cur)
        i += 1
        cur = _add_months(start, i)
    return out


def _empty_epss_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["cve_id", "epss_score", "epss_percentile"])


def run_multi_t0(args: argparse.Namespace) -> dict[str, Any]:
    """Aggregate distinct Label-A positive CVEs across many monthly t0 windows.

    Acquires ONE NVD universe and ONE synthetic fleet, then loops monthly t0s in
    the EPSS v3 era. The feasibility metric is the count of UNIQUE distinct positive
    CVEs across windows (NOT the per-window event sum, NOT the pair count).
    """
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0_start = parse_date(args.t0_start)
    t0_end = parse_date(args.t0_end)
    h = int(args.h_days)
    lookback = int(args.nvd_lookback_days)
    min_positive = int(args.min_positive_cves)
    skip_fetch = bool(args.skip_fetch)
    cached_only = bool(args.use_cached_only)
    api_key = (getattr(args, "nvd_api_key", None) or os.environ.get("NVD_API_KEY") or None)

    t0_list = _iter_t0s(t0_start, t0_end, args.t0_frequency)
    if not t0_list:
        raise ProbeBlocked(f"no t0 windows in range {t0_start}..{t0_end}")
    universe_start = min(t0_list) - timedelta(days=lookback)
    universe_end = max(t0_list)

    # --- acquire NVD universe ONCE (hardened/chunked/resumable) ---
    nvd_status: dict[str, Any] = {}
    try:
        nvd_records = _obtain_nvd(
            universe_start, universe_end, skip_fetch=skip_fetch, cached_only=cached_only,
            api_key=api_key, sleep_seconds=float(args.nvd_sleep_seconds),
            resume=bool(args.resume), status=nvd_status,
        )
    except ProbeBlocked:
        atomic_write_json(out / "nvd_acquisition_status.json",
                          nvd_status or {"blocked": True, "api_key_present": bool(api_key)})
        raise
    atomic_write_json(out / "nvd_acquisition_status.json", nvd_status)

    kev_raw = _obtain_kev(skip_fetch=skip_fetch, cached_only=cached_only)

    # --- normalize + catalog-match ONCE ---
    vulns_all, nvd_counts = _vulns_from_nvd(nvd_records)
    catalog_keys = _catalog_keys()
    vulns_matched = [v for v in vulns_all if _matches_catalog(v, catalog_keys)]

    # --- one fleet, reused across windows (reference t0 = latest) ---
    t0_ref = max(t0_list)
    hosts = FleetGenerator(
        fleet_size=int(args.fleet_size), seed=int(args.seed), t0=t0_ref
    ).generate()

    # --- per-window pass (cheap: labels + counts only) ---
    per_window: list[dict[str, Any]] = []
    epss_rows: list[dict[str, Any]] = []
    union_positive: set[str] = set()
    union_paired: set[str] = set()
    event_positive = 0
    for t0 in t0_list:
        horizon_end = t0 + timedelta(days=h)
        label_window_end = max(universe_end, horizon_end)
        vulns_for_pairs = [v for v in vulns_matched if v.disclosure_date <= t0]
        kev_label = kev_client.normalize_kev_catalog(kev_raw, as_of_date=label_window_end)
        kev_t0 = kev_client.normalize_kev_catalog(kev_raw, as_of_date=t0)
        try:
            epss_text = _obtain_epss_text(t0, skip_fetch=skip_fetch, cached_only=cached_only)
            epss_t0 = epss_client.normalize_epss_csv(epss_text, t0)
            epss_status = "present"
        except ProbeBlocked:
            epss_t0 = _empty_epss_frame()
            epss_status = "missing"

        pairs = build_pairs(vulns_for_pairs, hosts, t0)
        paired_cves = sorted({p.cve_id for p in pairs})
        labels = label_a(pairs, kev_label, None, t0, h, label_window_end)
        bools = [_label_bool(v) for v in list(labels)]
        pos_pairs = sum(1 for b in bools if b is True)
        neg_pairs = sum(1 for b in bools if b is False)
        pos_cves = sorted({p.cve_id for p, b in zip(pairs, bools, strict=True) if b is True})

        union_positive |= set(pos_cves)
        union_paired |= set(paired_cves)
        event_positive += len(pos_cves)

        present = (len(set(epss_t0["cve_id"]) & set(paired_cves))
                   if (paired_cves and not epss_t0.empty) else 0)
        cov = (present / len(paired_cves)) if paired_cves else 0.0
        epss_rows.append({"t0": t0.isoformat(), "epss_status": epss_status,
                          "paired_cves": len(paired_cves), "epss_present": present,
                          "coverage": cov})
        per_window.append({
            "t0": t0.isoformat(), "horizon_end": horizon_end.isoformat(),
            "vulns_disclosed_le_t0": len(vulns_for_pairs),
            "pairs_built": len(pairs), "distinct_cves_in_pairs": len(paired_cves),
            "positive_cves_this_window": len(pos_cves),
            "positive_pairs": pos_pairs, "negative_pairs": neg_pairs,
            "kev_asof_t0_count": (len(set(kev_t0["cve_id"])) if not kev_t0.empty else 0),
        })

    unique_positive_cves = len(union_positive)

    # --- calibration smoke (CVE-level dedup) only if the UNIQUE gate passes ---
    if unique_positive_cves >= min_positive:
        calib = _attempt_calibration_multi(
            t0_list=t0_list, vulns_matched=vulns_matched, hosts=hosts, kev_raw=kev_raw,
            union_positive=union_positive, seed=int(args.seed), out=out,
            skip_fetch=skip_fetch, cached_only=cached_only,
        )
    else:
        calib = {"attempted": False,
                 "reason": (f"unique positive distinct CVEs {unique_positive_cves} "
                            f"< min {min_positive}")}

    decision = _decide(unique_positive_cves, calib)

    aggregate = {
        "n_windows": len(t0_list),
        "t0_start": t0_start.isoformat(), "t0_end": t0_end.isoformat(),
        "universe_start": universe_start.isoformat(), "universe_end": universe_end.isoformat(),
        "nvd_lookback_days": lookback, "h_days": h,
        **nvd_counts,
        "catalog_matched_cves": len(vulns_matched),
        "union_distinct_cves_in_pairs": len(union_paired),
        "unique_positive_cves": unique_positive_cves,
        "unique_negative_cves": len(union_paired) - unique_positive_cves,
        "event_positive_cves_across_windows": event_positive,
    }

    # --- write outputs ---
    pd.DataFrame(per_window).to_csv(out / "per_t0_counts.csv", index=False)
    pd.DataFrame([{"metric": k, "value": v} for k, v in aggregate.items()]).to_csv(
        out / "aggregate_counts.csv", index=False)
    pd.DataFrame([
        {"stage": "total_nvd_records", "count": nvd_counts.get("total_nvd_records", 0)},
        {"stage": "normalized_cves", "count": nvd_counts.get("normalized_cves", 0)},
        {"stage": "cves_with_cpe", "count": nvd_counts.get("cves_with_cpe", 0)},
        {"stage": "catalog_matched_cves", "count": len(vulns_matched)},
        {"stage": "union_distinct_cves_in_pairs", "count": len(union_paired)},
        {"stage": "unique_positive_cves", "count": unique_positive_cves},
    ]).to_csv(out / "cve_match_counts.csv", index=False)
    pd.DataFrame([
        {"label": "unique_positive_cves", "count": unique_positive_cves},
        {"label": "unique_negative_cves", "count": len(union_paired) - unique_positive_cves},
        {"label": "event_positive_cves_across_windows", "count": event_positive},
        {"label": "union_distinct_cves_in_pairs", "count": len(union_paired)},
    ]).to_csv(out / "label_counts.csv", index=False)
    pd.DataFrame(epss_rows).to_csv(out / "epss_coverage.csv", index=False)
    atomic_write_json(out / "calibration_status.json", calib)
    atomic_write_json(out / "decision_gate.json", {
        "metric": "unique_positive_distinct_cves",
        "value": unique_positive_cves,
        "min_required_for_go": min_positive,
        "calibration_non_degenerate": calib.get("non_degenerate"),
        "decision": decision,
        "note": ("Gate uses UNIQUE distinct positive CVEs across windows. "
                 "event_positive_cves_across_windows is NOT the calibration sample "
                 "size (a CVE positive in multiple windows is one calibration unit)."),
    })

    summary = {
        "mode": "multi_t0",
        "params": {
            "t0_start": t0_start.isoformat(), "t0_end": t0_end.isoformat(),
            "t0_frequency": args.t0_frequency, "h_days": h,
            "nvd_lookback_days": lookback, "fleet_size": int(args.fleet_size),
            "seed": int(args.seed), "min_positive_cves": min_positive,
            "use_cached_only": cached_only, "skip_fetch": skip_fetch,
            "aggregate_positive_cves": bool(getattr(args, "aggregate_positive_cves", True)),
            "nvd_api_key_present": bool(api_key),
        },
        "aggregate": aggregate,
        "per_window": per_window,
        "calibration": calib,
        "nvd_acquisition": nvd_status,
        "decision": decision,
        "note": ("Multi-t0 feasibility probe only; NOT a calibrated result, NOT a paper "
                 "claim. Synthetic fleet + public feeds (NVD/EPSS/KEV); PoC license-gated "
                 "and off. The gating metric is UNIQUE distinct positive CVEs. Paper 1 "
                 "frozen outputs untouched."),
    }
    atomic_write_json(out / "summary.json", summary)
    _write_multi_summary_md(out / "summary.md", summary)
    return summary


def _attempt_calibration_multi(
    *, t0_list, vulns_matched, hosts, kev_raw, union_positive, seed, out,
    skip_fetch, cached_only,
) -> dict[str, Any]:
    """CVE-level deduped calibration smoke over the multi-t0 universe.

    Builds features per window, deduplicates to one row per CVE (so a CVE present
    in several windows is a single calibration unit), labels by membership in the
    aggregated positive set, and fits weights. Non-degeneracy only; no perf claims.
    """
    feat_by_cve: dict[str, dict[str, float]] = {}
    for t0 in t0_list:
        vulns_for_pairs = [v for v in vulns_matched if v.disclosure_date <= t0]
        if not vulns_for_pairs:
            continue
        kev_t0 = kev_client.normalize_kev_catalog(kev_raw, as_of_date=t0)
        try:
            epss_text = _obtain_epss_text(t0, skip_fetch=skip_fetch, cached_only=cached_only)
            epss_t0 = epss_client.normalize_epss_csv(epss_text, t0)
        except ProbeBlocked:
            epss_t0 = _empty_epss_frame()
        pairs = build_pairs(vulns_for_pairs, hosts, t0)
        if not pairs:
            continue
        pair_frame = pairs_to_frame(pairs)
        try:
            ff = _build_features(pairs, pair_frame, vulns_for_pairs, hosts,
                                 epss_t0, kev_t0, t0, seed)
        except Exception as exc:
            return {"attempted": False, "reason": f"feature build failed: {exc}"}
        ff = ff.drop_duplicates(subset=["cve_id"])
        for _, row in ff.iterrows():
            feat_by_cve.setdefault(row["cve_id"],
                                   {c: float(row[c]) for c in FEATURE_COLUMNS})

    if len(feat_by_cve) < 4:
        return {"attempted": False, "reason": f"CVE-level frame <4 rows ({len(feat_by_cve)})"}
    rows = [{"pair_id": cve, "cve_id": cve, **feats, "label": cve in union_positive}
            for cve, feats in feat_by_cve.items()]
    frame = pd.DataFrame(rows).reset_index(drop=True)
    if frame["label"].nunique() < 2:
        return {"attempted": False, "reason": "single-class CVE-level frame"}

    y = pd.Series(frame["label"].astype(bool).to_numpy(), dtype="boolean")
    times = [t0_list[0]] * len(frame)
    rng = make_rng(derive_subseed(seed, "probe|multit0|split"))
    split = pd.Series(["train" if rng.random() < 0.7 else "test" for _ in range(len(frame))])
    if (split == "train").sum() < 2 or y[split.to_numpy() == "train"].nunique() < 2:
        split = pd.Series(["train"] * len(frame))

    result: dict[str, Any] = {"attempted": True, "n_cves": len(frame),
                              "positives": int(y.sum()),
                              "reason": "gate passed (multi-t0, CVE-level dedup)"}
    result.update(_run_fits(frame, y, times, split, seed, out))
    return result


def _write_multi_summary_md(path: Path, summary: dict) -> None:
    a = summary["aggregate"]
    lines = ["# Paper 2 multi-t0 feasibility probe summary", "",
             "**Feasibility probe only; not a calibrated result, not a paper claim.**", "",
             f"- params: {json.dumps(summary['params'])}", "",
             "## Aggregate counts (gating metric: UNIQUE distinct positive CVEs)", ""]
    for k, v in a.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Per-window positive CVEs", ""]
    for w in summary["per_window"]:
        lines.append(f"- {w['t0']}: positive_cves_this_window={w['positive_cves_this_window']}, "
                     f"distinct_cves_in_pairs={w['distinct_cves_in_pairs']}, "
                     f"pairs_built={w['pairs_built']}")
    lines += ["", "## Calibration", "", f"- {json.dumps(summary['calibration'])}", "",
              f"## Probe decision: **{summary['decision']}**", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_md(path: Path, summary: dict) -> None:
    c = summary["counts"]
    lines = ["# Paper 2 feasibility probe summary", "",
             "**Feasibility probe only; not a calibrated result, not a paper claim.**", "",
             f"- params: {json.dumps(summary['params'])}", "",
             "## Counts", ""]
    for k, v in c.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Calibration", "", f"- {json.dumps(summary['calibration'])}", "",
              f"## Probe decision: **{summary['decision']}**", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Paper 2 public-feed feasibility probe.")
    p.add_argument("--start-date", default="2023-06-01")
    p.add_argument("--end-date", default="2024-09-30")
    p.add_argument("--t0", default="2024-09-01")
    p.add_argument("--h-days", type=int, default=30)
    p.add_argument("--fleet-size", type=int, default=500)
    p.add_argument("--seed", type=int, default=20260601)
    p.add_argument("--out", default="paper2/feasibility/probe_v1")
    p.add_argument("--use-cached-only", action="store_true")
    p.add_argument("--skip-fetch", action="store_true")
    p.add_argument("--min-positive-cves", type=int, default=50)
    p.add_argument("--epss-sample-days", type=int, default=3)
    p.add_argument("--include-poc", action="store_true")
    # --- hardened NVD acquisition ---
    p.add_argument("--nvd-api-key", default=None,
                   help="NVD API key (falls back to NVD_API_KEY env).")
    p.add_argument("--nvd-sleep-seconds", type=float, default=6.0,
                   help="Polite pause between NVD chunk requests "
                        "(NVD recommends ~6s unauthenticated, ~0.6s with a key).")
    p.add_argument("--resume", action="store_true",
                   help="Reuse per-chunk NVD caches (resume an interrupted fetch).")
    # --- multi-t0 feasibility mode ---
    p.add_argument("--multi-t0", action="store_true",
                   help="Aggregate distinct positive CVEs across monthly t0 windows.")
    p.add_argument("--t0-start", default="2023-09-01")
    p.add_argument("--t0-end", default="2025-02-01")
    p.add_argument("--t0-frequency", default="monthly", choices=["monthly"])
    p.add_argument("--nvd-lookback-days", type=int, default=730,
                   help="NVD disclosure lookback before the earliest t0 (universe span).")
    p.add_argument("--aggregate-positive-cves", action="store_true", default=True,
                   help="Count UNIQUE distinct positive CVEs across windows (default).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    multi = bool(getattr(args, "multi_t0", False))
    try:
        summary = run_multi_t0(args) if multi else run_probe(args)
    except ProbeBlocked as exc:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        blocker = {"blocked": True, "reason": str(exc),
                   "decision": "CONDITIONAL_GO_pending_data_acquisition",
                   "note": "Public-feed fetch blocked and no cache; NOT a failure of the method."}
        atomic_write_json(out / "summary.json", blocker)
        (out / "summary.md").write_text(
            f"# Paper 2 feasibility probe — BLOCKED\n\n{exc}\n\n"
            "Decision: CONDITIONAL GO pending data acquisition (no fake success).\n",
            encoding="utf-8")
        print(f"BLOCKED: {exc}")
        print("Decision: CONDITIONAL GO pending data acquisition (rerun with cache or network).")
        return 3
    except PoCLicenseGateError as exc:
        print(f"REFUSED: {exc}")
        return 2

    if summary.get("mode") == "multi_t0":
        print("=== Paper 2 MULTI-t0 feasibility probe ===")
        print(f"  params: {summary['params']}")
        a = summary["aggregate"]
        for k in ("n_windows", "total_nvd_records", "catalog_matched_cves",
                  "union_distinct_cves_in_pairs", "unique_positive_cves",
                  "event_positive_cves_across_windows"):
            print(f"  {k}: {a.get(k)}")
    else:
        print("=== Paper 2 feasibility probe ===")
        print(f"  out:                       {summary['params']}")
        c = summary["counts"]
        for k in ("total_nvd_records", "catalog_matched_cves", "distinct_cves_in_pairs",
                  "label_a_positive_cves", "positive_pairs", "kev_future_label_count"):
            print(f"  {k}: {c.get(k)}")
    print(f"  calibration: {summary['calibration'].get('attempted')} "
          f"(non_degenerate={summary['calibration'].get('non_degenerate')})")
    print(f"  PROBE DECISION: {summary['decision']}")
    print("NOTE: feasibility probe only; not a paper result; Paper 1 untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
