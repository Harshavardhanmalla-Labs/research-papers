"""End-to-end no-leakage integration test (Phase 3 fleet + Phase 4 pairs/labels)."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from paper1.audit.schema import Vulnerability, VulnerabilityHostPair
from paper1.feeds.kev_client import normalize_kev_catalog
from paper1.feeds.poc_client import normalize_exploitdb_csv
from paper1.model.frames import attach_labels, attach_split, pairs_to_frame
from paper1.model.labels import label_a, label_b, label_dates_a
from paper1.model.pairs import build_pairs
from paper1.model.splits import assign_split, make_temporal_split, validate_split_gap
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.utils.time import parse_date

FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"

T0 = date(2025, 6, 1)
H = 30
WINDOW_START = date(2024, 6, 1)
WINDOW_END = date(2026, 5, 31)


def _load_toy_vulns() -> list[Vulnerability]:
    raw = json.loads((FIXTURES / "vulnerabilities_toy.json").read_text(encoding="utf-8"))
    vulns = []
    for d in raw:
        kwargs = {k: v for k, v in d.items() if not k.startswith("_")}
        kwargs["disclosure_date"] = parse_date(kwargs["disclosure_date"])
        kwargs["feed_fetch_timestamp"] = datetime.fromisoformat(
            kwargs["feed_fetch_timestamp"].replace("Z", "+00:00")
        )
        vulns.append(Vulnerability(**kwargs))
    return vulns


def _load_toy_kev() -> pd.DataFrame:
    raw = json.loads((FIXTURES / "kev_toy.json").read_text(encoding="utf-8"))
    # Use window_end as as_of so all events through the window are retained.
    return normalize_kev_catalog(raw, as_of_date=WINDOW_END)


def _load_toy_poc() -> pd.DataFrame:
    text = (FIXTURES / "poc_toy.csv").read_text(encoding="utf-8")
    return normalize_exploitdb_csv(text, as_of_date=WINDOW_END)


def test_fixtures_load():
    assert len(_load_toy_vulns()) == 5
    assert not _load_toy_kev().empty
    assert not _load_toy_poc().empty


def test_no_future_disclosure_in_pairs():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=100, seed=1, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    cve_ids = {p.cve_id for p in pairs}
    # CVE-2026-1003 is disclosed in 2026 (> t0) and must not appear.
    assert "CVE-2026-1003" not in cve_ids
    # CVE-2024-1004 has no matching product and must not appear.
    assert "CVE-2024-1004" not in cve_ids


def test_pairs_exist_for_common_products():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=200, seed=1, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    cve_ids = {p.cve_id for p in pairs}
    # openssl (exact) and sqlite (fuzzy) are widely installed in the fleet.
    assert "CVE-2024-1001" in cve_ids
    assert "CVE-2024-1002" in cve_ids


def test_every_pair_validates_schema():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=100, seed=1, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    for p in pairs:
        assert isinstance(p, VulnerabilityHostPair)
        assert p.first_observed.tzinfo is not None


def test_pair_count_deterministic_under_seed():
    vulns = _load_toy_vulns()
    a = build_pairs(vulns, FleetGenerator(fleet_size=150, seed=5, t0=T0).generate(), T0)
    b = build_pairs(vulns, FleetGenerator(fleet_size=150, seed=5, t0=T0).generate(), T0)
    assert [p.pair_id for p in a] == [p.pair_id for p in b]


def test_labels_respect_temporal_cutoff():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=200, seed=1, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    kev = _load_toy_kev()
    poc = _load_toy_poc()

    a = label_a(pairs, kev, poc, T0, H, WINDOW_END)
    b = label_b(pairs, poc, T0, H, WINDOW_END)
    a_dates = label_dates_a(pairs, kev, poc, T0, H, WINDOW_END)

    # CVE-2024-1001 enters KEV on 2025-06-15 (inside window) -> Label A positive.
    cve_for_pair = [p.cve_id for p in pairs]
    a_by_cve = dict(zip(cve_for_pair, a.tolist(), strict=True))
    if "CVE-2024-1001" in a_by_cve:
        assert a_by_cve["CVE-2024-1001"] is True

    # CVE-2024-1002 has a PoC on 2025-06-20 (inside) -> Label A and B positive.
    b_by_cve = dict(zip(cve_for_pair, b.tolist(), strict=True))
    if "CVE-2024-1002" in b_by_cve:
        assert b_by_cve["CVE-2024-1002"] is True

    # Every positive Label A date must lie strictly after t0 and at most t0+H.
    from datetime import timedelta

    horizon_end = T0 + timedelta(days=H)
    for d in a_dates:
        if d is pd.NA or d is None or (isinstance(d, float) and pd.isna(d)):
            continue
        assert T0 < d <= horizon_end


def test_temporal_split_gap_at_least_h():
    cfg = make_temporal_split(None, WINDOW_START, WINDOW_END, H, train_months=18)
    validate_split_gap(cfg, H)
    assert (cfg["gap_end"] - cfg["train_end"]).days >= H
    # t0 = 2025-06-01 falls in the train window.
    assert assign_split(T0, cfg) == "train"


def test_censored_label_near_window_end_is_na():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=50, seed=1, t0=date(2026, 5, 20)).generate()
    pairs = build_pairs(vulns, hosts, date(2026, 5, 20))
    kev = _load_toy_kev()
    poc = _load_toy_poc()
    # t0 + H = 2026-06-19 > window_end 2026-05-31 -> all censored.
    a = label_a(pairs, kev, poc, date(2026, 5, 20), H, WINDOW_END)
    if len(a) > 0:
        assert a.isna().all()


def test_full_pipeline_frame_assembly():
    vulns = _load_toy_vulns()
    hosts = FleetGenerator(fleet_size=200, seed=1, t0=T0).generate()
    pairs = build_pairs(vulns, hosts, T0)
    frame = pairs_to_frame(pairs)
    a = label_a(pairs, _load_toy_kev(), _load_toy_poc(), T0, H, WINDOW_END)
    a_dates = label_dates_a(pairs, _load_toy_kev(), _load_toy_poc(), T0, H, WINDOW_END)
    frame = attach_labels(frame, a, a_dates, label_name="A")

    cfg = make_temporal_split(None, WINDOW_START, WINDOW_END, H)
    splits = [assign_split(T0, cfg)] * len(frame)
    frame = attach_split(frame, splits)

    assert "label_A" in frame.columns
    assert "label_A_date" in frame.columns
    assert "split" in frame.columns
    assert (frame["split"] == "train").all()
