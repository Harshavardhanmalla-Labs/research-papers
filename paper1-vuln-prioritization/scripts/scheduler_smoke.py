#!/usr/bin/env python3
"""Scheduler smoke: fleet -> pairs -> features -> rank -> schedule_window.

No metrics, no EEHDA, no experiments. No remediation is performed.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from paper1.audit.hash_chain import AuditLogger
from paper1.audit.schema import ExploitSignal, Vulnerability
from paper1.feeds.cve_client import parse_cpe23
from paper1.model.features import build_feature_frame
from paper1.model.frames import pairs_to_frame
from paper1.model.pairs import build_pairs
from paper1.model.strategies import rank_pairs
from paper1.scheduler.approver import ApproverPolicyA
from paper1.scheduler.blackout import load_blackout_config
from paper1.scheduler.scheduler import schedule_window
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
SEED = 1
NOW = datetime(2025, 6, 10, 10, 0, tzinfo=UTC)  # Tuesday business hours


def _t0_dt() -> datetime:
    return datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)


def _load_vulns():
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


def main() -> int:
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
    crit = [
        compute_criticality(
            host=host_by_id[hid], host_defaults=defaults,
            identity_config="ad_entra_default", cmdb_staleness_rate=0.0,
            rng=make_rng(derive_subseed(SEED, f"crit|{hid}")), computed_at=_t0_dt(),
        )
        for hid in sorted({p.host_id for p in pairs})
    ]
    exposures, complexities = [], []
    for p in pairs:
        vuln = vuln_by_cve[p.cve_id]
        parsed = parse_cpe23(vuln.cpe_matches[0])
        pk = (parsed.vendor.lower(), parsed.product.lower())
        meta = product_by_key.get(pk)
        exposures.append(compute_exposure(
            vulnerability=vuln, host=host_by_id[p.host_id], product_meta=meta,
            product_key=pk, service_catalog=services,
            rng=make_rng(derive_subseed(SEED, f"expo|{p.pair_id}")),
        ))
        complexities.append(compute_complexity(
            vuln, host_by_id[p.host_id], meta, make_rng(derive_subseed(SEED, f"cmplx|{p.pair_id}"))
        ))
    signals = [
        ExploitSignal(
            cve_id=cve, epss_score=float(make_rng(derive_subseed(SEED, f"sig|{cve}")).random()),
            epss_percentile=0.5, epss_fetch_timestamp=_t0_dt(), epss_version="v4",
            kev_status=False, poc_observed=False, signal_staleness_days=0,
        )
        for cve in sorted({p.cve_id for p in pairs})
    ]
    feature_frame = build_feature_frame(pair_frame, vulns, signals, crit, exposures, complexities, T0)
    ranked = rank_pairs("proposed_full", pair_frame, feature_frame)
    ranked = ranked.copy()
    ranked["host_role"] = ranked["host_id"].map({h.host_id: h.role for h in hosts})
    ranked["group_id"] = ranked["host_id"].map({h.host_id: h.group_id for h in hosts})
    ranked["kev_due_date"] = None
    ranked["complexity_score"] = ranked["pair_id"].map({c.pair_id: c.complexity_score for c in complexities})
    ranked["bundle_group"] = None

    audit_path = Path(tempfile.mkdtemp(prefix="paper1_sched_")) / "audit.jsonl"
    logger = AuditLogger(audit_path)
    res = schedule_window(
        ranked, capacity=20, now=NOW, blackout_config=load_blackout_config("primary"),
        approver_policy=ApproverPolicyA(seed=SEED), audit_logger=logger,
        group_caps={"standard_workstation": 5}, seed=SEED,
    )
    ok, issues = logger.verify_chain()

    print(f"ranked pairs:    {len(ranked)}")
    print(f"scheduled:       {len(res.scheduled)}")
    print(f"deferred:        {len(res.deferred)}")
    print(f"accepted_risk:   {len(res.accepted_risk)}")
    print(f"escalations:     {len(res.escalations)}")
    print(f"used_capacity:   {res.used_capacity}/{res.capacity}")
    print(f"audit log path:  {res.audit_log_path}")
    print(f"verify_chain:    {ok} (issues={issues})")
    print("NOTE: no remediation performed; scheduling and recording only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
