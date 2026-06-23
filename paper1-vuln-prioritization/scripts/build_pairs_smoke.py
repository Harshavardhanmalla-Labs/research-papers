#!/usr/bin/env python3
"""Smoke driver: build pairs from a synthetic fleet + toy vulnerabilities.

No live feed calls, no scoring, no scheduler, no metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from paper1.audit.schema import Vulnerability
from paper1.feeds.kev_client import normalize_kev_catalog
from paper1.feeds.poc_client import normalize_exploitdb_csv
from paper1.model.labels import censor_mask, label_a, label_b
from paper1.model.pairs import build_pairs
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.utils.time import parse_date

FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"
WINDOW_END = parse_date("2026-05-31")


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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build vulnerability-host pairs (smoke).")
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--t0", default="2025-06-01")
    p.add_argument("--h-days", type=int, default=30)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    t0 = parse_date(args.t0)

    vulns = _load_vulns()
    hosts = FleetGenerator(fleet_size=args.size, seed=args.seed, t0=t0).generate()
    pairs = build_pairs(vulns, hosts, t0)

    kev = normalize_kev_catalog(
        json.loads((FIXTURES / "kev_toy.json").read_text(encoding="utf-8")),
        as_of_date=WINDOW_END,
    )
    poc = normalize_exploitdb_csv(
        (FIXTURES / "poc_toy.csv").read_text(encoding="utf-8"),
        as_of_date=WINDOW_END,
    )

    a = label_a(pairs, kev, poc, t0, args.h_days, WINDOW_END)
    b = label_b(pairs, poc, t0, args.h_days, WINDOW_END)
    censored = censor_mask(pairs, t0, args.h_days, WINDOW_END)

    def _count_true(series: pd.Series) -> int:
        return int(series.fillna(False).astype(bool).sum())

    print(f"pairs:            {len(pairs)}")
    print(f"label_A positives:{_count_true(a)}")
    print(f"label_B positives:{_count_true(b)}")
    print(f"censored:         {int(censored.fillna(False).astype(bool).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
