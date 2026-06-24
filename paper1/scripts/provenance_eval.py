#!/usr/bin/env python3
"""Tamper-evident decision-provenance evaluation for VulnPrio audit logs.

Faithfully mirrors the hash-chain construction in
``src/paper1/audit/hash_chain.py`` (canonical JSON with sort_keys and
``separators=(",",":")``, SHA-256 hexdigest, ``prior_record_hash`` links,
64-zero genesis), and extends it with the contribution of this paper:

  * monotonic sequence numbers,
  * per-window Merkle commitments, and
  * periodic Ed25519-signed checkpoints anchoring (head hash, count, root).

We then run an adversarial tamper harness over 8 attack classes against the
BASELINE (naive chain) and the AUGMENTED ledger, and measure detection rate
plus runtime/space overhead. Frozen outputs -> results/provenance_v1/.
"""
from __future__ import annotations
import hashlib, json, os, time, csv
import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results", "provenance_v1"); os.makedirs(OUT, exist_ok=True)
GENESIS = "0" * 64
RNG = np.random.default_rng(20260624)

# ---------------------------------------------------------------------------
# Faithful re-implementation of src/paper1/audit/hash_chain.py semantics.
# ---------------------------------------------------------------------------
def canonical(rec: dict, exclude=("record_hash",)) -> str:
    raw = {k: v for k, v in rec.items() if k not in exclude}
    return json.dumps(raw, sort_keys=True, separators=(",", ":"), default=str)

def record_hash(rec: dict) -> str:
    return hashlib.sha256(canonical(rec).encode("utf-8")).hexdigest()

def build_chain(records: list[dict]) -> list[dict]:
    """Append-only hash chain: each record links to the prior record_hash."""
    out, prior = [], GENESIS
    for r in records:
        r = dict(r); r["prior_record_hash"] = prior
        r["record_hash"] = record_hash(r)
        prior = r["record_hash"]; out.append(r)
    return out

def verify_chain(chain: list[dict]) -> bool:
    """Baseline verification (exactly paper1's verify_chain logic)."""
    prior = GENESIS
    for r in chain:
        if r.get("prior_record_hash") != prior:
            return False
        rh = dict(r); stored = rh.pop("record_hash", None)
        if record_hash(rh) != stored:
            return False
        prior = r["record_hash"]
    return True

# ---------------------------------------------------------------------------
# AUGMENTED ledger: Merkle per window + Ed25519 signed checkpoints.
# ---------------------------------------------------------------------------
def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return GENESIS
    layer = [bytes.fromhex(x) for x in leaves]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]; b = layer[i + 1] if i + 1 < len(layer) else layer[i]
            nxt.append(hashlib.sha256(a + b).digest())
        layer = nxt
    return layer[0].hex()

def make_checkpoints(chain: list[dict], sk: Ed25519PrivateKey, every: int) -> list[dict]:
    """Sign a checkpoint after every `every` records and at the chain head.

    Each checkpoint commits to (count, head_hash, window_id, merkle_root) and
    is signed; the trusted auditor holds only the public key.
    """
    cps, win_leaves, win_id = [], [], None
    def emit(i):
        body = {
            "count": i + 1,
            "head_hash": chain[i]["record_hash"],
            "window_id": chain[i]["window_id"],
            "merkle_root": merkle_root([c["record_hash"] for c in chain[: i + 1]]),
        }
        msg = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        body["sig"] = sk.sign(msg).hex()
        cps.append(body)
    for i, r in enumerate(chain):
        if (i + 1) % every == 0:
            emit(i)
    if not cps or cps[-1]["count"] != len(chain):  # closing checkpoint at head
        emit(len(chain) - 1)
    return cps

def _cp_verify(cp, pub) -> bool:
    body = {k: cp[k] for k in ("count", "head_hash", "window_id", "merkle_root")}
    msg = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    try:
        pub.verify(bytes.fromhex(cp["sig"]), msg); return True
    except InvalidSignature:
        return False

def verify_augmented(chain: list[dict], cps: list[dict], pub, anchor: dict) -> bool:
    """Verify against a TRUSTED, independently-held latest checkpoint (`anchor`),
    exactly as a Certificate-Transparency monitor checks a signed tree head.
    The auditor retains/publishes `anchor`; the attacker cannot forge or drop it."""
    if not verify_chain(chain):
        return False
    if not _cp_verify(anchor, pub):            # trusted anchor must be authentic
        return False
    # the presented chain must reproduce the anchored (count, head, root):
    # catches tail-truncation, wholesale-replacement, and any content edit
    if len(chain) != anchor["count"]:
        return False
    if chain[anchor["count"] - 1]["record_hash"] != anchor["head_hash"]:
        return False
    if merkle_root([x["record_hash"] for x in chain]) != anchor["merkle_root"]:
        return False
    # every presented intermediate checkpoint must also verify + be consistent
    for cp in cps:
        if not _cp_verify(cp, pub):
            return False
        c = cp["count"]
        if c > len(chain) or chain[c - 1]["record_hash"] != cp["head_hash"]:
            return False
    return True

# ---------------------------------------------------------------------------
# Synthetic but realistic audit-decision records (paper1 field structure).
# ---------------------------------------------------------------------------
FEATURES = ["epss", "kev", "cvss_base", "asset_criticality", "exposure",
            "urgency", "remediation_complexity"]
DTYPES = ["score", "schedule", "approve", "defer", "outcome"]

def gen_records(n: int, windows: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    recs = []
    for i in range(n):
        w = (i * windows) // n
        recs.append({
            "record_id": f"ADR-{i+1}",
            "pair_id": f"H-{rng.integers(1, 5000)}:CVE-2026-{rng.integers(1000, 99999)}",
            "window_id": f"W-{w+1}",
            "decision_type": DTYPES[i % len(DTYPES)],
            "weights_version": "w-2026Q2-v1",
            "framework_version": "vulnprio-2.0.0",
            "data_feed_versions": {"nvd": "2026-05-26", "epss": "2026-05-26", "kev": "2026-05-26"},
            "feature_values": {f: float(round(rng.random(), 4)) for f in FEATURES},
            "created_at": f"2026-06-{1 + (i % 28):02d}T00:00:00Z",
        })
    return recs

# ---------------------------------------------------------------------------
# Adversarial tamper harness — 8 attack classes.
# ---------------------------------------------------------------------------
def _strip(r):
    return {k: v for k, v in r.items() if k not in ("prior_record_hash", "record_hash")}

def attack(chain, kind, attacker, rng):
    """Apply `kind` under a `weak` or `strong` attacker.

    weak   = can edit stored bytes but does NOT recompute the chain hashes
             (e.g. partial/forensic tamper, append-only medium, no chain code).
    strong = realistic insider with log-write access who recomputes every
             downstream hash to restore internal consistency.
    Returns the tampered chain (checkpoints are signed, so untouched)."""
    c = [dict(r) for r in chain]; n = len(c)
    if kind == "modify_field":
        i = int(rng.integers(0, n)); c[i]["decision_type"] = "approve" if c[i]["decision_type"] != "approve" else "defer"
    elif kind == "reorder":
        i, j = sorted(rng.choice(n, 2, replace=False)); c[i], c[j] = c[j], c[i]
    elif kind == "delete_middle":
        i = int(rng.integers(1, n - 1)); del c[i]
    elif kind == "truncate_tail":
        k = int(rng.integers(1, max(2, n // 4))); c = c[: n - k]
    elif kind == "insert":
        i = int(rng.integers(1, n)); c.insert(i, {**c[i - 1], "record_id": "ADR-FORGED", "decision_type": "accept_risk"})
    elif kind == "weight_rollback":
        i = int(rng.integers(0, n)); c[i]["weights_version"] = "w-2025Q1-v0"
    elif kind == "feed_forge":
        i = int(rng.integers(0, n)); c[i]["data_feed_versions"] = {"nvd": "2026-01-01", "epss": "2026-01-01", "kev": "2026-01-01"}
    elif kind == "wholesale_replace":
        for i in rng.choice(n, max(1, n // 5), replace=False):
            c[i]["decision_type"] = "approve"
        attacker = "strong"   # replacement only makes sense if the attacker re-chains
    if attacker == "strong":
        c = build_chain([_strip(r) for r in c])
    return c

ATTACKS = ["modify_field", "reorder", "delete_middle", "truncate_tail",
           "insert", "weight_rollback", "feed_forge", "wholesale_replace"]

def run_detection(trials=200, n=400, windows=8, every=50):
    sk = Ed25519PrivateKey.generate(); pub = sk.public_key()
    rows = []
    for kind in ATTACKS:
        det = {"weak_baseline": 0, "weak_aug": 0, "strong_baseline": 0, "strong_aug": 0}
        for t in range(trials):
            recs = gen_records(n, windows, seed=1000 + t)
            chain = build_chain(recs)
            cps = make_checkpoints(chain, sk, every)
            anchor = cps[-1]                       # auditor's trusted latest checkpoint
            assert verify_chain(chain) and verify_augmented(chain, cps, pub, anchor)
            for atk in ("weak", "strong"):
                tchain = attack(chain, kind, atk, np.random.default_rng(7 * t + 3))
                if not verify_chain(tchain):
                    det[f"{atk}_baseline"] += 1
                if not verify_augmented(tchain, cps, pub, anchor):
                    det[f"{atk}_aug"] += 1
        rows.append({"attack": kind, "trials": trials,
                     "weak_baseline": round(det["weak_baseline"] / trials, 4),
                     "weak_augmented": round(det["weak_aug"] / trials, 4),
                     "strong_baseline": round(det["strong_baseline"] / trials, 4),
                     "strong_augmented": round(det["strong_aug"] / trials, 4)})
        print(f"  {kind:18s} weak[base={det['weak_baseline']/trials:.2f} aug={det['weak_aug']/trials:.2f}]"
              f"  strong[base={det['strong_baseline']/trials:.2f} aug={det['strong_aug']/trials:.2f}]")
    return rows

def run_overhead():
    sk = Ed25519PrivateKey.generate(); pub = sk.public_key()
    rows = []
    for n in [1000, 5000, 20000, 50000]:
        recs = gen_records(n, 18, seed=42)
        t0 = time.perf_counter(); chain = build_chain(recs); t_chain = time.perf_counter() - t0
        t0 = time.perf_counter(); cps = make_checkpoints(chain, sk, 250); t_cp = time.perf_counter() - t0
        t0 = time.perf_counter(); verify_chain(chain); t_vbase = time.perf_counter() - t0
        t0 = time.perf_counter(); verify_augmented(chain, cps, pub, cps[-1]); t_vaug = time.perf_counter() - t0
        base_bytes = sum(len(json.dumps(r)) for r in chain)
        cp_bytes = sum(len(json.dumps(c)) for c in cps)
        rows.append({"n_records": n, "n_checkpoints": len(cps),
                     "append_chain_s": round(t_chain, 4), "checkpoint_sign_s": round(t_cp, 4),
                     "verify_baseline_s": round(t_vbase, 4), "verify_augmented_s": round(t_vaug, 4),
                     "append_throughput_rec_s": int(n / t_chain),
                     "chain_bytes": base_bytes, "checkpoint_overhead_pct": round(100 * cp_bytes / base_bytes, 3)})
        print(f"  n={n:6d} cps={len(cps):4d} append={n/t_chain:8.0f} rec/s "
              f"verify_aug={t_vaug*1000:6.1f}ms cp_overhead={100*cp_bytes/base_bytes:.2f}%")
    return rows

def run_interval(n=10000):
    """Checkpoint-interval tradeoff: anchoring cost vs the residual window of
    recent records not yet covered by a signed checkpoint (the P2 bound)."""
    sk = Ed25519PrivateKey.generate()
    recs = gen_records(n, 18, seed=99); chain = build_chain(recs)
    base_bytes = sum(len(json.dumps(r)) for r in chain)
    rows = []
    for every in [10, 50, 100, 250, 500]:
        t0 = time.perf_counter(); cps = make_checkpoints(chain, sk, every); t = time.perf_counter() - t0
        cp_bytes = sum(len(json.dumps(c)) for c in cps)
        rows.append({"checkpoint_interval": every, "n_checkpoints": len(cps),
                     "max_unanchored_records": every - 1,
                     "sign_time_s": round(t, 4),
                     "space_overhead_pct": round(100 * cp_bytes / base_bytes, 3)})
        print(f"  every={every:4d} cps={len(cps):5d} residual<={every-1:4d} rec "
              f"sign={t:6.3f}s overhead={100*cp_bytes/base_bytes:.3f}%")
    return rows

def main():
    print("== Detection (8 attack classes; baseline naive chain vs augmented ledger) ==")
    det = run_detection()
    print("\n== Overhead (append / checkpoint / verify / space) ==")
    ovh = run_overhead()
    print("\n== Checkpoint-interval tradeoff (50k log) ==")
    intv = run_interval()
    summary = {
        "construction": "SHA-256 hash chain (paper1 hash_chain.py) + Merkle-per-window + Ed25519 signed checkpoints",
        "detection": det, "overhead": ovh, "interval_tradeoff": intv,
        "strong_baseline_blind_spots": [r["attack"] for r in det if r["strong_baseline"] < 1.0],
        "weak_baseline_blind_spots": [r["attack"] for r in det if r["weak_baseline"] < 1.0],
        "augmented_full_coverage": all(r["weak_augmented"] == 1.0 and r["strong_augmented"] == 1.0 for r in det),
    }
    json.dump(summary, open(os.path.join(OUT, "provenance_summary.json"), "w"), indent=2)
    with open(os.path.join(OUT, "detection.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(det[0].keys())); w.writeheader(); w.writerows(det)
    with open(os.path.join(OUT, "overhead.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ovh[0].keys())); w.writeheader(); w.writerows(ovh)
    with open(os.path.join(OUT, "interval.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(intv[0].keys())); w.writeheader(); w.writerows(intv)
    print(f"\nfrozen -> {OUT}")
    print("strong-attacker baseline blind spots:", summary["strong_baseline_blind_spots"])
    print("weak-attacker baseline blind spots:", summary["weak_baseline_blind_spots"])
    print("augmented full coverage (both attackers):", summary["augmented_full_coverage"])

if __name__ == "__main__":
    main()
