"""End-to-end strategy integration (Phase 3 fleet -> features -> all strategies)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from paper1.audit.schema import ExploitSignal, Vulnerability
from paper1.feeds.kev_client import normalize_kev_catalog
from paper1.feeds.poc_client import normalize_exploitdb_csv
from paper1.model.features import build_feature_frame
from paper1.model.frames import pairs_to_frame
from paper1.model.labels import label_a
from paper1.model.pairs import build_pairs
from paper1.model.strategies import STRATEGY_NAMES, rank_pairs
from paper1.synthetic.catalogs import (
    load_host_type_defaults,
    load_product_catalog,
    load_service_catalog,
)
from paper1.synthetic.criticality import compute_criticality
from paper1.synthetic.exposure import compute_exposure
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.synthetic.remediation_complexity import compute_complexity
from paper1.utils.seeds import derive_subseed, make_rng
from paper1.utils.time import parse_date

FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"
T0 = date(2025, 6, 1)
H = 30
WINDOW_END = date(2026, 5, 31)
SEED = 1


def _t0_dt() -> datetime:
    return datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)


def _load_vulns() -> list[Vulnerability]:
    raw = json.loads((FIXTURES / "vulnerabilities_toy.json").read_text(encoding="utf-8"))
    out = []
    for d in raw:
        kwargs = {k: v for k, v in d.items() if not k.startswith("_")}
        kwargs["disclosure_date"] = parse_date(kwargs["disclosure_date"])
        kwargs["feed_fetch_timestamp"] = datetime.fromisoformat(
            kwargs["feed_fetch_timestamp"].replace("Z", "+00:00")
        )
        out.append(Vulnerability(**kwargs))
    return out


def _synthetic_signals(cve_ids: list[str]) -> list[ExploitSignal]:
    """Create deterministic ExploitSignal records (KEV=False as of t0)."""
    signals = []
    for cve in sorted(set(cve_ids)):
        rng = make_rng(derive_subseed(SEED, f"signal|{cve}"))
        signals.append(
            ExploitSignal(
                cve_id=cve,
                epss_score=float(rng.random()),
                epss_percentile=float(rng.random()),
                epss_fetch_timestamp=_t0_dt(),
                epss_version="v4",
                kev_status=False,  # KEV additions in fixtures are all >= t0
                poc_observed=False,
                signal_staleness_days=0,
            )
        )
    return signals


def _build_everything():
    vulns = _load_vulns()
    hosts = FleetGenerator(fleet_size=100, seed=SEED, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    pair_frame = pairs_to_frame(pairs)

    host_by_id = {h.host_id: h for h in hosts}
    vuln_by_cve = {v.cve_id: v for v in vulns}
    defaults = load_host_type_defaults()
    services = load_service_catalog()
    product_by_key = {
        (p["vendor"].lower(), p["product"].lower()): p
        for p in load_product_catalog()["products"]
    }

    # Criticality per host that appears in pairs.
    crit = []
    for hid in sorted({p.host_id for p in pairs}):
        rng = make_rng(derive_subseed(SEED, f"crit|{hid}"))
        crit.append(
            compute_criticality(
                host=host_by_id[hid],
                host_defaults=defaults,
                identity_config="ad_entra_default",
                cmdb_staleness_rate=0.0,
                rng=rng,
                computed_at=_t0_dt(),
            )
        )

    # Exposure + complexity per pair.
    exposures = []
    complexities = []
    for p in pairs:
        host = host_by_id[p.host_id]
        vuln = vuln_by_cve[p.cve_id]
        # derive product_key from the vuln's first CPE for meta lookup
        from paper1.feeds.cve_client import parse_cpe23

        parsed = parse_cpe23(vuln.cpe_matches[0])
        pk = (parsed.vendor.lower(), parsed.product.lower())
        meta = product_by_key.get(pk)
        rng_e = make_rng(derive_subseed(SEED, f"expo|{p.pair_id}"))
        exposures.append(
            compute_exposure(
                vulnerability=vuln,
                host=host,
                product_meta=meta,
                product_key=pk,
                service_catalog=services,
                rng=rng_e,
            )
        )
        rng_c = make_rng(derive_subseed(SEED, f"cmplx|{p.pair_id}"))
        complexities.append(compute_complexity(vuln, host, meta, rng_c))

    signals = _synthetic_signals([p.cve_id for p in pairs])
    feature_frame = build_feature_frame(
        pair_frame, vulns, signals, crit, exposures, complexities, T0
    )
    labels = label_a(pairs, _load_kev(), _load_poc(), T0, H, WINDOW_END)
    return pair_frame, feature_frame, labels, pairs


def _load_kev() -> pd.DataFrame:
    raw = json.loads((FIXTURES / "kev_toy.json").read_text(encoding="utf-8"))
    return normalize_kev_catalog(raw, as_of_date=WINDOW_END)


def _load_poc() -> pd.DataFrame:
    return normalize_exploitdb_csv(
        (FIXTURES / "poc_toy.csv").read_text(encoding="utf-8"), as_of_date=WINDOW_END
    )


def test_all_strategies_return_consistent_pair_counts():
    pair_frame, feature_frame, labels, _ = _build_everything()
    n = len(pair_frame)
    for name in STRATEGY_NAMES:
        if name == "gbt_comparator":
            continue
        kw = {"seed": SEED}
        if name == "oracle":
            kw["label_series"] = labels
        out = rank_pairs(name, pair_frame, feature_frame, **kw)
        assert len(out) == n, name
        assert set(out["pair_id"]) == set(pair_frame["pair_id"]), name
        assert out["rank"].tolist() == list(range(1, n + 1)), name


def test_no_duplicate_pairs_in_any_strategy():
    pair_frame, feature_frame, labels, _ = _build_everything()
    for name in STRATEGY_NAMES:
        if name == "gbt_comparator":
            continue
        kw = {"seed": SEED}
        if name == "oracle":
            kw["label_series"] = labels
        out = rank_pairs(name, pair_frame, feature_frame, **kw)
        assert not out["pair_id"].duplicated().any(), name


def test_strategies_deterministic_under_same_seed():
    pair_frame, feature_frame, labels, _ = _build_everything()
    a = rank_pairs("random", pair_frame, feature_frame, seed=7)
    b = rank_pairs("random", pair_frame, feature_frame, seed=7)
    assert a["pair_id"].tolist() == b["pair_id"].tolist()
    c = rank_pairs("proposed_full", pair_frame, feature_frame)
    d = rank_pairs("proposed_full", pair_frame, feature_frame)
    assert c["pair_id"].tolist() == d["pair_id"].tolist()


def test_no_nan_priority_scores():
    pair_frame, feature_frame, labels, _ = _build_everything()
    for name in ["random", "epss_only", "kev_first", "proposed_full", "cve_max"]:
        out = rank_pairs(name, pair_frame, feature_frame, seed=SEED)
        assert not out["priority_score"].isna().any(), name


def test_oracle_ranks_label_a_positives_first():
    pair_frame, feature_frame, labels, _ = _build_everything()
    out = rank_pairs("oracle", pair_frame, feature_frame, label_series=labels)
    n_pos = int(labels.fillna(False).astype(bool).sum())
    assert n_pos > 0  # toy fixtures guarantee some positives
    top = out.head(n_pos)
    # Every top-ranked pair must be a positive.
    pos_pairs = set(pair_frame.loc[labels.fillna(False).astype(bool).to_numpy(), "pair_id"])
    assert set(top["pair_id"]) == pos_pairs


def test_proposed_full_has_feature_contributions_available():
    pair_frame, feature_frame, labels, _ = _build_everything()
    from paper1.model.scoring import score_pairs_linear
    from paper1.model.weights import get_weights

    scored = score_pairs_linear(feature_frame, get_weights("w_logit_placeholder"))
    assert "feature_contributions" in scored.columns
    # contributions reconstruct the score
    from paper1.model.weights import FEATURE_COLUMNS

    row = scored.iloc[0]
    contrib_sum = sum(row[f"contribution_{f}"] for f in FEATURE_COLUMNS)
    assert contrib_sum == _approx(row["priority_score"])


def _approx(x, tol=1e-9):
    import pytest

    return pytest.approx(x, abs=tol)
