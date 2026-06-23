"""Tests for the Paper 2 public-feed feasibility probe.

No network: feed fetchers, the fleet generator, and the feature builder are
monkeypatched with tiny deterministic fixtures. Verifies counts, CPE/catalog
matching, Label A timing semantics, the calibration gate, PoC gating, output
writing, and that Paper 1's frozen outputs are not modified.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from paper1.audit.schema import Host, InstalledSoftware, PatchState

_PROBE_PATH = Path("scripts/paper2_feasibility_probe.py")
_DT = datetime(2024, 1, 1, tzinfo=UTC)


def _load_probe():
    spec = importlib.util.spec_from_file_location("p2probe", _PROBE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sw(vendor: str, product: str, version: str = "1.0") -> InstalledSoftware:
    return InstalledSoftware(
        cpe=f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*",
        product=product, vendor=vendor, version=version,
    )


def _host(host_id: str, cpes: list[tuple[str, str]], remediated=()) -> Host:
    return Host(
        host_id=host_id, os_family="linux", os_version="x", role="member_server",
        network_zone="internal", identity_tier="tier_2", data_sensitivity_proxy="general",
        installed_software=[_sw(v, p) for v, p in cpes],
        patch_state=PatchState(last_scan=_DT, scan_source="test", remediated_cves=list(remediated)),
        last_seen_per_source={"scan": _DT}, group_id="G1",
    )


def _fake_fleet(hosts):
    class _FakeGen:
        def __init__(self, **kwargs):  # accepts fleet_size/seed/t0/...
            pass

        def generate(self):
            return hosts
    return _FakeGen


def _norm_factory(records_by_id: dict[str, dict]):
    """Return a fake normalize_nvd_record using a fixture dict keyed by cve_id."""
    def _norm(rec):
        r = records_by_id[rec["cve_id"]]
        row = {
            "cve_id": r["cve_id"], "cwe_ids": [], "cpe_matches": [r["cpe"]],
            "cvss_v4_vector": None, "cvss_v4_base": None,
            "cvss_v31_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "cvss_v31_base": r.get("cvss", 7.5), "cvss_version_used": "v31",
            "disclosure_date": __import__("paper1.utils.time", fromlist=["parse_date"]).parse_date(r["published"]),
            "vendor_advisory_refs": [], "mitigations_listed": [], "preconditions": {},
        }
        return row, []
    return _norm


def _epss_bytes(cve_ids: list[str]) -> bytes:
    lines = ["#model_version:v3,score_date:2024-09-01", "cve,epss,percentile"]
    lines += [f"{c},0.5,0.9" for c in cve_ids]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _kev_raw(entries: list[tuple[str, str]]) -> dict:
    return {"catalogVersion": "test", "vulnerabilities": [
        {"cveID": c, "vendorProject": "v", "product": "p", "vulnerabilityName": "n",
         "dateAdded": d, "requiredAction": "patch", "dueDate": d} for c, d in entries]}


def _patch_feeds(monkeypatch, probe, *, records, kev_entries, epss_cves, hosts,
                 build_features_stub=None):
    rec_by_id = {r["cve_id"]: r for r in records}
    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window",
                        lambda s, e, **k: [{"cve_id": r["cve_id"]} for r in records])
    monkeypatch.setattr("paper1.feeds.nvd_client.normalize_nvd_record", _norm_factory(rec_by_id))
    monkeypatch.setattr("paper1.feeds.kev_client.fetch_kev_catalog", lambda **k: _kev_raw(kev_entries))
    monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv", lambda d, **k: _epss_bytes(epss_cves))
    monkeypatch.setattr(probe, "FleetGenerator", _fake_fleet(hosts))
    if build_features_stub is not None:
        monkeypatch.setattr(probe, "_build_features", build_features_stub)


def _run(probe, tmp_path, monkeypatch, *, records, kev_entries, epss_cves, hosts,
         min_positive=50, build_features_stub=None, extra_args=None):
    # Isolate the probe cache to tmp so tests never write fake data into the
    # real data/cache/paper2_probe directory.
    monkeypatch.setattr(probe, "_CACHE_DIR", tmp_path / "cache")
    _patch_feeds(monkeypatch, probe, records=records, kev_entries=kev_entries,
                 epss_cves=epss_cves, hosts=hosts, build_features_stub=build_features_stub)
    out = tmp_path / "probe"
    args = ["--out", str(out), "--t0", "2024-09-01", "--h-days", "30",
            "--start-date", "2024-07-01", "--end-date", "2024-09-30",  # <=120 days: single NVD chunk
            "--fleet-size", "10", "--seed", "1", "--epss-sample-days", "1",
            "--min-positive-cves", str(min_positive)]
    if extra_args:
        args += extra_args
    rc = probe.main(args)
    summary_path = out / "summary.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else None
    )
    return rc, summary, out


# t0 = 2024-09-01, horizon (t0, t0+30] = (2024-09-01, 2024-10-01]


def test_basic_run_and_outputs_written(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [
        {"cve_id": "CVE-2024-0001", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"},
    ]
    rc, summary, out = _run(
        probe, tmp_path, monkeypatch,
        records=records, kev_entries=[("CVE-2024-0001", "2024-09-10")],
        epss_cves=["CVE-2024-0001"], hosts=[_host("H1", [("openssl", "openssl")])],
    )
    assert rc == 0
    for f in ("summary.json", "summary.md", "cve_match_counts.csv",
              "label_counts.csv", "epss_coverage.csv", "calibration_status.json"):
        assert (out / f).exists(), f
    assert summary["counts"]["pairs_built"] >= 1


def test_cpe_catalog_matching(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [
        {"cve_id": "CVE-2024-0001", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"},
        {"cve_id": "CVE-2024-0002", "cpe": "cpe:2.3:a:acme:widget:1.0:*:*:*:*:*:*:*", "published": "2024-07-01"},
    ]
    _, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[], epss_cves=[], hosts=[_host("H1", [("openssl", "openssl")])],
    )
    # openssl is in the catalog; acme/widget is not.
    assert summary["counts"]["catalog_matched_cves"] == 1
    assert summary["counts"]["distinct_cves_in_pairs"] == 1


def test_future_kev_event_is_label_positive(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [{"cve_id": "CVE-2024-0010", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    # KEV added 2024-09-10, inside (2024-09-01, 2024-10-01] -> positive
    _, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0010", "2024-09-10")], epss_cves=["CVE-2024-0010"],
        hosts=[_host("H1", [("openssl", "openssl")])],
    )
    assert summary["counts"]["label_a_positive_cves"] == 1
    assert summary["counts"]["positive_pairs"] >= 1
    assert summary["counts"]["kev_future_label_count"] == 1


def test_kev_before_t0_is_feature_not_future_label(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [{"cve_id": "CVE-2024-0020", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    # KEV added 2024-06-01, BEFORE t0 -> feature K, not a future-window label
    _, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0020", "2024-06-01")], epss_cves=["CVE-2024-0020"],
        hosts=[_host("H1", [("openssl", "openssl")])],
    )
    assert summary["counts"]["kev_asof_t0_count"] == 1          # feature K present
    assert summary["counts"]["kev_future_label_count"] == 0     # not a future label
    assert summary["counts"]["label_a_positive_cves"] == 0


def test_cve_disclosed_after_t0_excluded_from_pairs(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [
        {"cve_id": "CVE-2024-0030", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"},
        {"cve_id": "CVE-2024-0031", "cpe": "cpe:2.3:a:openssl:openssl:3.1:*:*:*:*:*:*:*", "published": "2024-09-15"},  # after t0
    ]
    _, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records, kev_entries=[],
        epss_cves=[], hosts=[_host("H1", [("openssl", "openssl")])],
    )
    assert summary["counts"]["distinct_cves_in_pairs"] == 1  # only the pre-t0 CVE


def test_insufficient_positives_blocks_calibration(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [{"cve_id": "CVE-2024-0040", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    _, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0040", "2024-09-10")], epss_cves=["CVE-2024-0040"],
        hosts=[_host("H1", [("openssl", "openssl")])], min_positive=50,
    )
    assert summary["calibration"]["attempted"] is False
    assert "min" in summary["calibration"]["reason"]


def test_enough_positives_triggers_calibration(tmp_path, monkeypatch):
    probe = _load_probe()
    # 6 openssl CVEs: 3 KEV-in-window (positive), 3 not (negative).
    records = [{"cve_id": f"CVE-2024-01{i:02d}", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*",
                "published": "2024-07-01"} for i in range(6)]
    kev = [(f"CVE-2024-01{i:02d}", "2024-09-10") for i in range(3)]  # first 3 positive

    def _stub_features(pairs, pair_frame, vulns_for_pairs, hosts, epss_t0, kev_t0, t0, seed):
        rows = []
        for p in pairs:
            n = int(p.cve_id[-2:])
            rows.append({"pair_id": p.pair_id, "cve_id": p.cve_id,
                         "E": 0.1 * (n + 1), "K": 1.0 if n < 3 else 0.0, "S": 0.5,
                         "C": 0.3 + 0.05 * n, "X": 0.2, "U": 0.4, "R": 0.1 * n})
        return pd.DataFrame(rows)

    _, summary, out = _run(
        probe, tmp_path, monkeypatch, records=records, kev_entries=kev,
        epss_cves=[r["cve_id"] for r in records],
        hosts=[_host("H1", [("openssl", "openssl")]), _host("H2", [("openssl", "openssl")])],
        min_positive=1, build_features_stub=_stub_features,
    )
    assert summary["counts"]["label_a_positive_cves"] == 3
    assert summary["calibration"]["attempted"] is True
    assert summary["calibration"]["n_cves"] == 6


def test_poc_disabled_by_default(tmp_path, monkeypatch):
    probe = _load_probe()
    # If PoC were fetched, this would error; default include_poc=False must skip it.
    monkeypatch.setattr("paper1.feeds.poc_client.fetch_poc_index",
                        lambda **k: (_ for _ in ()).throw(AssertionError("PoC fetched")))
    records = [{"cve_id": "CVE-2024-0050", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    rc, summary, _ = _run(
        probe, tmp_path, monkeypatch, records=records, kev_entries=[],
        epss_cves=[], hosts=[_host("H1", [("openssl", "openssl")])],
    )
    assert rc == 0  # ran without touching PoC


def test_include_poc_without_gate_fails_clearly(tmp_path, monkeypatch):
    probe = _load_probe()
    monkeypatch.delenv("PAPER1_ENABLE_POC_FETCH", raising=False)
    records = [{"cve_id": "CVE-2024-0060", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    rc, _, _ = _run(
        probe, tmp_path, monkeypatch, records=records, kev_entries=[],
        epss_cves=[], hosts=[_host("H1", [("openssl", "openssl")])],
        extra_args=["--include-poc"],
    )
    assert rc == 2  # PoCLicenseGateError -> clean refusal


def test_paper1_frozen_output_not_modified(tmp_path, monkeypatch):
    probe = _load_probe()
    frozen = Path("results/primary_full_v1/FREEZE_MANIFEST.json")
    before = frozen.stat().st_mtime_ns if frozen.exists() else None
    records = [{"cve_id": "CVE-2024-0070", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-07-01"}]
    _run(probe, tmp_path, monkeypatch, records=records,
         kev_entries=[("CVE-2024-0070", "2024-09-10")], epss_cves=["CVE-2024-0070"],
         hosts=[_host("H1", [("openssl", "openssl")])])
    after = frozen.stat().st_mtime_ns if frozen.exists() else None
    assert before == after  # Paper 1 freeze untouched (or absent in both)


# ---------------------------------------------------------------------------
# Step 3.6 — hardened NVD acquisition (chunking, dedup, 429, resume)
# ---------------------------------------------------------------------------


def test_nvd_chunking_splits_at_120_days_and_dedups(tmp_path, monkeypatch):
    probe = _load_probe()
    monkeypatch.setattr(probe, "_CACHE_DIR", tmp_path / "cache")
    calls: list[tuple[date, date]] = []

    def _fetch(s, e, **k):
        calls.append((s, e))
        return [{"cve": {"id": "CVE-2024-9999"}}]  # same id in every chunk

    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _fetch)
    recs = probe._obtain_nvd(date(2024, 1, 1), date(2024, 9, 1),
                             skip_fetch=False, cached_only=False, sleep_seconds=0.0)
    # 2024-01-01..2024-09-01 = 244 days -> 3 chunks of <=120 days
    assert len(calls) == 3
    assert all((e - s).days <= 119 for s, e in calls)
    assert len(recs) == 1  # deduplicated by CVE id across chunks
    assert len(list((tmp_path / "cache").glob("nvd_chunk_*.json"))) == 3


def test_nvd_429_preserves_completed_chunks_and_blocks(tmp_path, monkeypatch):
    probe = _load_probe()
    monkeypatch.setattr(probe, "_CACHE_DIR", tmp_path / "cache")
    n = {"i": 0}

    def _fetch(s, e, **k):
        n["i"] += 1
        if n["i"] >= 2:  # second chunk hits the unauthenticated rate limit
            raise RuntimeError("HTTP Error 429: Too Many Requests")
        return [{"cve": {"id": f"CVE-2024-00{n['i']:02d}"}}]

    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _fetch)
    status: dict = {}
    with pytest.raises(probe.ProbeBlocked):
        probe._obtain_nvd(date(2024, 1, 1), date(2024, 9, 1), skip_fetch=False,
                          cached_only=False, sleep_seconds=0.0, status=status)
    assert status["blocked"] is True
    assert status["completed_chunks"] == 1
    assert "resume_command" in status and "--resume" in status["resume_command"]
    # the completed chunk is cached so a resume does not refetch it
    assert len(list((tmp_path / "cache").glob("nvd_chunk_*.json"))) == 1


def test_nvd_resume_reuses_cached_chunks_without_refetch(tmp_path, monkeypatch):
    probe = _load_probe()
    monkeypatch.setattr(probe, "_CACHE_DIR", tmp_path / "cache")
    n = {"i": 0}

    def _fetch_ok(s, e, **k):
        n["i"] += 1
        return [{"cve": {"id": f"CVE-2024-01{n['i']:02d}"}}]

    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _fetch_ok)
    recs1 = probe._obtain_nvd(date(2024, 1, 1), date(2024, 9, 1), skip_fetch=False,
                              cached_only=False, sleep_seconds=0.0)
    assert len(recs1) == 3 and n["i"] == 3

    def _fetch_boom(s, e, **k):
        raise AssertionError("resume must not refetch cached chunks")

    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _fetch_boom)
    recs2 = probe._obtain_nvd(date(2024, 1, 1), date(2024, 9, 1), skip_fetch=False,
                              cached_only=False, sleep_seconds=0.0, resume=True)
    assert len(recs2) == 3  # served entirely from per-chunk cache


# ---------------------------------------------------------------------------
# Step 3.6 — multi-t0 aggregation (unique vs event positives, CVE-level dedup)
# ---------------------------------------------------------------------------


def _run_multi(probe, tmp_path, monkeypatch, *, records, kev_entries, hosts,
               t0_start, t0_end, h_days, lookback, min_positive=50,
               epss_cves=None, epss_raises=False, build_features_stub=None,
               extra_args=None):
    monkeypatch.setattr(probe, "_CACHE_DIR", tmp_path / "cache")
    rec_by_id = {r["cve_id"]: r for r in records}
    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window",
                        lambda s, e, **k: [{"cve_id": r["cve_id"]} for r in records])
    monkeypatch.setattr("paper1.feeds.nvd_client.normalize_nvd_record", _norm_factory(rec_by_id))
    monkeypatch.setattr("paper1.feeds.kev_client.fetch_kev_catalog", lambda **k: _kev_raw(kev_entries))
    if epss_raises:
        monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv",
                            lambda d, **k: (_ for _ in ()).throw(RuntimeError("EPSS unavailable")))
    else:
        monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv",
                            lambda d, **k: _epss_bytes(epss_cves or []))
    monkeypatch.setattr(probe, "FleetGenerator", _fake_fleet(hosts))
    if build_features_stub is not None:
        monkeypatch.setattr(probe, "_build_features", build_features_stub)
    out = tmp_path / "probe_multi"
    args = ["--multi-t0", "--out", str(out), "--t0-start", t0_start, "--t0-end", t0_end,
            "--t0-frequency", "monthly", "--h-days", str(h_days),
            "--nvd-lookback-days", str(lookback), "--fleet-size", "10", "--seed", "1",
            "--nvd-sleep-seconds", "0", "--min-positive-cves", str(min_positive)]
    if extra_args:
        args += extra_args
    rc = probe.main(args)
    summary_path = out / "summary.json"
    summary = (json.loads(summary_path.read_text(encoding="utf-8"))
               if summary_path.exists() else None)
    return rc, summary, out


def test_multi_t0_unique_positive_counted_once_event_counted_per_window(tmp_path, monkeypatch):
    probe = _load_probe()
    # One CVE whose KEV addition (2024-07-10) lands inside BOTH overlapping 45-day
    # horizons of t0=2024-06-01 and t0=2024-07-01 -> positive in 2 windows.
    records = [{"cve_id": "CVE-2024-0001",
                "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"}]
    rc, summary, out = _run_multi(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0001", "2024-07-10")], epss_cves=["CVE-2024-0001"],
        hosts=[_host("H1", [("openssl", "openssl")])],
        t0_start="2024-06-01", t0_end="2024-07-01", h_days=45, lookback=60, min_positive=50,
    )
    assert rc == 0
    a = summary["aggregate"]
    assert a["n_windows"] == 2
    assert a["unique_positive_cves"] == 1                     # deduped across windows
    assert a["event_positive_cves_across_windows"] == 2       # positive in each window
    assert (out / "per_t0_counts.csv").exists()
    assert (out / "aggregate_counts.csv").exists()
    assert (out / "decision_gate.json").exists()
    assert (out / "nvd_acquisition_status.json").exists()


def test_multi_t0_aggregates_distinct_positives_across_windows(tmp_path, monkeypatch):
    probe = _load_probe()
    # Three CVEs each becoming KEV in a different month -> 3 unique positives.
    records = [
        {"cve_id": "CVE-2024-0001", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"},
        {"cve_id": "CVE-2024-0002", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"},
        {"cve_id": "CVE-2024-0003", "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"},
    ]
    kev = [("CVE-2024-0001", "2024-06-10"), ("CVE-2024-0002", "2024-07-10"),
           ("CVE-2024-0003", "2024-08-10")]
    rc, summary, _ = _run_multi(
        probe, tmp_path, monkeypatch, records=records, kev_entries=kev,
        epss_cves=[r["cve_id"] for r in records], hosts=[_host("H1", [("openssl", "openssl")])],
        t0_start="2024-06-01", t0_end="2024-08-01", h_days=30, lookback=60, min_positive=50,
    )
    assert rc == 0
    a = summary["aggregate"]
    assert a["n_windows"] == 3
    assert a["unique_positive_cves"] == 3
    assert a["union_distinct_cves_in_pairs"] == 3


def test_multi_t0_insufficient_unique_positives_blocks_calibration(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [{"cve_id": "CVE-2024-0001",
                "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"}]
    _, summary, _ = _run_multi(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0001", "2024-06-10")], epss_cves=["CVE-2024-0001"],
        hosts=[_host("H1", [("openssl", "openssl")])],
        t0_start="2024-06-01", t0_end="2024-07-01", h_days=30, lookback=60, min_positive=50,
    )
    assert summary["calibration"]["attempted"] is False
    assert "min" in summary["calibration"]["reason"]
    assert summary["decision"] == "PIVOT_away_from_calibration"


def test_multi_t0_calibration_cve_level_dedup_no_inflation(tmp_path, monkeypatch):
    probe = _load_probe()
    # 6 CVEs disclosed before both t0s -> present in BOTH windows' pairs. CVE-level
    # dedup must yield n_cves == 6 (NOT 12). 3 are KEV-in-window-1 (positive).
    records = [{"cve_id": f"CVE-2024-00{i:02d}",
                "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"}
               for i in range(6)]
    kev = [(f"CVE-2024-00{i:02d}", "2024-06-10") for i in range(3)]  # positive in window 1

    def _stub_features(pairs, pair_frame, vulns_for_pairs, hosts, epss_t0, kev_t0, t0, seed):
        rows = []
        for p in pairs:
            n = int(p.cve_id[-2:])
            rows.append({"pair_id": p.pair_id, "cve_id": p.cve_id,
                         "E": 0.1 * (n + 1), "K": 1.0 if n < 3 else 0.0, "S": 0.5,
                         "C": 0.3 + 0.05 * n, "X": 0.2, "U": 0.4, "R": 0.1 * n})
        return pd.DataFrame(rows)

    _, summary, _ = _run_multi(
        probe, tmp_path, monkeypatch, records=records, kev_entries=kev,
        epss_cves=[r["cve_id"] for r in records], hosts=[_host("H1", [("openssl", "openssl")])],
        t0_start="2024-06-01", t0_end="2024-07-01", h_days=30, lookback=60,
        min_positive=1, build_features_stub=_stub_features,
    )
    assert summary["aggregate"]["unique_positive_cves"] == 3
    assert summary["calibration"]["attempted"] is True
    assert summary["calibration"]["n_cves"] == 6      # deduped (not 6*2 windows)
    assert summary["calibration"]["positives"] == 3


def test_multi_t0_epss_optional_when_snapshot_missing(tmp_path, monkeypatch):
    probe = _load_probe()
    records = [{"cve_id": "CVE-2024-0001",
                "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"}]
    rc, summary, out = _run_multi(
        probe, tmp_path, monkeypatch, records=records,
        kev_entries=[("CVE-2024-0001", "2024-06-10")], epss_raises=True,
        hosts=[_host("H1", [("openssl", "openssl")])],
        t0_start="2024-06-01", t0_end="2024-07-01", h_days=30, lookback=60, min_positive=50,
    )
    assert rc == 0  # missing EPSS does not block the label measurement
    cov = pd.read_csv(out / "epss_coverage.csv")
    assert (cov["epss_status"] == "missing").all()


def test_multi_t0_paper1_frozen_output_not_modified(tmp_path, monkeypatch):
    probe = _load_probe()
    frozen = Path("results/primary_full_v1/FREEZE_MANIFEST.json")
    before = frozen.stat().st_mtime_ns if frozen.exists() else None
    records = [{"cve_id": "CVE-2024-0001",
                "cpe": "cpe:2.3:a:openssl:openssl:3.0:*:*:*:*:*:*:*", "published": "2024-05-15"}]
    _run_multi(probe, tmp_path, monkeypatch, records=records,
               kev_entries=[("CVE-2024-0001", "2024-06-10")], epss_cves=["CVE-2024-0001"],
               hosts=[_host("H1", [("openssl", "openssl")])],
               t0_start="2024-06-01", t0_end="2024-07-01", h_days=30, lookback=60)
    after = frozen.stat().st_mtime_ns if frozen.exists() else None
    assert before == after
