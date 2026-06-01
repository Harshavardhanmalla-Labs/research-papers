#!/usr/bin/env python3
"""Generate a synthetic fleet bundle and write it to JSONL files.

No vulnerabilities, no scores, no scheduling decisions are produced.
Intended for smoke runs and for downstream-phase development.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from paper1.synthetic.fleet_generator import generate_synthetic_fleet_bundle
from paper1.utils.io import write_jsonl
from paper1.utils.logging import get_logger, log_with_context
from paper1.utils.time import parse_date


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a synthetic fleet bundle.")
    p.add_argument("--size", type=int, default=100, help="Number of hosts (default: 100)")
    p.add_argument("--seed", type=int, default=1, help="Master seed (default: 1)")
    p.add_argument(
        "--identity-config",
        default="ad_entra_default",
        choices=("ad_entra_default", "federated"),
        help="Identity mapping configuration (default: ad_entra_default)",
    )
    p.add_argument(
        "--t0", default="2026-05-31", help="Reference date YYYY-MM-DD (default: 2026-05-31)"
    )
    p.add_argument(
        "--out",
        default="results/synthetic",
        help="Output directory (default: results/synthetic)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    log = get_logger("paper1.scripts.generate_synthetic_fleet")
    t0 = parse_date(args.t0)

    bundle = generate_synthetic_fleet_bundle(
        fleet_size=args.size,
        seed=args.seed,
        identity_config=args.identity_config,
        t0=t0,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    hosts_path = out_dir / "hosts.jsonl"
    criticality_path = out_dir / "criticality.jsonl"

    write_jsonl(
        hosts_path,
        [h.model_dump(mode="json") for h in bundle["hosts"]],
    )
    write_jsonl(
        criticality_path,
        [c.model_dump(mode="json") for c in bundle["criticality"]],
    )

    log_with_context(
        log,
        logging.INFO,
        "synthetic fleet written",
        size=args.size,
        seed=args.seed,
        identity_config=args.identity_config,
        hosts_path=str(hosts_path),
        criticality_path=str(criticality_path),
    )
    print(f"hosts: {len(bundle['hosts'])} -> {hosts_path}")
    print(f"criticality: {len(bundle['criticality'])} -> {criticality_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
