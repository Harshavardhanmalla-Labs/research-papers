#!/usr/bin/env python3
"""Parse the CyberLab Cowrie honeynet dataset into a per-session table.

Source: Sedlar, Kren, Stefanic Juznic, Volk (2020). CyberLab honeynet dataset.
        Zenodo. https://doi.org/10.5281/zenodo.3687527  (CC BY 4.0)

For each SSH/Telnet attack session we derive:
  * EARLY-PHASE behavioral-cognitive features  -- signals available from the
    connection + client fingerprint + authentication phase, i.e. BEFORE the
    attacker commits to a command / tunnel / download.  These are the only
    features the BCI model is allowed to use (no leakage from the action phase).
  * The session's dominant ATT&CK-aligned INTENT label, derived from the FULL
    session via a transparent priority mapping (download > tunnel > execution >
    brute-force).  Labels are read from observed events only -- never invented.

Writes data/processed/sessions.csv  +  prints distribution stats.
"""
import gzip, json, os, re, glob, csv, collections
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw")
OUT_DIR = os.path.join(HERE, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

ACTION_EVENTS = {"cowrie.command.success", "cowrie.command.failed",
                 "cowrie.direct-tcpip.request", "cowrie.direct-tcpip.data",
                 "cowrie.session.file_download", "cowrie.session.file_upload"}
PORT_RE = re.compile(r":(\d{1,5})(?:\s|\]|$)")
CMD_RE  = re.compile(r"Command (?:found|not found): (.*)")
COMMON_USERS = {"root", "admin", "user", "test", "oracle", "ubuntu", "pi", "guest", "support"}


def ts(s):
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def first_port(msg):
    m = PORT_RE.search(msg or "")
    return int(m.group(1)) if m and int(m.group(1)) <= 65535 else None


def parse_session(sid, events, date):
    events = [e for e in events if e.get("eventid")]
    events.sort(key=lambda e: e.get("timestamp") or "")
    eids = [e["eventid"] for e in events]

    # --- protocol / client fingerprint (early) ---
    ssh_ver = next((e.get("ssh_client_version") for e in events if e.get("ssh_client_version")), None)
    proto = "ssh" if (ssh_ver or "cowrie.client.version" in eids) else "telnet"
    cv = next((e for e in events if e.get("eventid") == "cowrie.client.version"), {})
    n_enc = len(cv.get("encCS") or [])
    n_kex = len(cv.get("kexAlgs") or [])
    n_mac = len(cv.get("macCS") or [])
    n_key = len(cv.get("keyAlgs") or [])
    has_hassh = 1 if any(e.get("hassh") for e in events) else 0

    # --- authentication behavior (early) ---
    logins = [e for e in events if e.get("eventid", "").startswith("cowrie.login")]
    creds, pw_lens, empty_pw, common_user = set(), [], 0, 0
    for e in logins:
        u, p = (e.get("username") or ""), (e.get("password") or "")
        creds.add((u, p))
        pw_lens.append(len(p))
        if p == "":
            empty_pw = 1
        if u.lower() in COMMON_USERS:
            common_user = 1
    n_auth = len(logins)
    n_auth_ok = sum(1 for e in logins if e.get("eventid") == "cowrie.login.success")

    # --- timing (early) ---
    times = [ts(e.get("timestamp")) for e in events if ts(e.get("timestamp"))]
    t0 = times[0] if times else None
    first_action_idx = next((i for i, e in enumerate(events) if e["eventid"] in ACTION_EVENTS), None)
    if first_action_idx is not None and t0:
        ta = ts(events[first_action_idx].get("timestamp"))
        time_to_action = (ta - t0).total_seconds() if ta else 0.0
    else:
        time_to_action = 0.0
    n_early_events = first_action_idx if first_action_idx is not None else len(events)
    hour = t0.hour if t0 else 0

    # --- ACTION phase -> defines the label (full session, observed) ---
    n_cmd = sum(1 for e in events if e["eventid"] in ("cowrie.command.success", "cowrie.command.failed"))
    n_cmd_fail = sum(1 for e in events if e["eventid"] == "cowrie.command.failed")
    n_tcpip = sum(1 for e in events if e["eventid"] == "cowrie.direct-tcpip.request")
    tunnel_ports = [first_port(e.get("message")) for e in events if e["eventid"] == "cowrie.direct-tcpip.request"]
    tunnel_ports = [p for p in tunnel_ports if p]
    n_dl = sum(1 for e in events if e["eventid"] == "cowrie.session.file_download")
    dur = next((e.get("duration") for e in events if e.get("eventid") == "cowrie.session.closed" and e.get("duration")), None)

    if n_dl > 0:
        intent = "malware_delivery"      # T1105 Ingress Tool Transfer
    elif n_tcpip > 0:
        intent = "tunneling"             # T1090 Proxy / relay abuse
    elif n_cmd > 0:
        intent = "execution"             # T1059 Command execution / recon
    else:
        intent = "bruteforce"            # T1110 Brute force only

    return {
        "session_id": sid, "date": date, "sensor": next((e.get("sensor") for e in events if e.get("sensor")), ""),
        # early-phase features (model inputs)
        "proto": proto, "ssh_ver": (ssh_ver or "")[:60], "n_enc": n_enc, "n_kex": n_kex,
        "n_mac": n_mac, "n_key": n_key, "has_hassh": has_hassh,
        "n_auth": n_auth, "n_auth_ok": n_auth_ok, "n_distinct_creds": len(creds),
        "max_pw_len": max(pw_lens) if pw_lens else 0, "empty_pw": empty_pw, "common_user": common_user,
        "hour": hour, "time_to_action": round(time_to_action, 2), "n_early_events": n_early_events,
        # action-phase (label provenance / analysis only -- NOT model inputs)
        "n_cmd": n_cmd, "n_cmd_fail": n_cmd_fail, "n_tcpip": n_tcpip,
        "tunnel_port": (collections.Counter(tunnel_ports).most_common(1)[0][0] if tunnel_ports else 0),
        "n_download": n_dl, "duration": round(dur, 2) if dur else 0.0,
        "intent": intent,
    }


def main():
    rows = []
    for fp in sorted(glob.glob(os.path.join(RAW, "cyberlab_*.json.gz"))):
        date = re.search(r"(\d{4}-\d{2}-\d{2})", fp).group(1)
        data = json.load(gzip.open(fp))
        n0 = len(rows)
        for d in data:
            for sid, events in d.items():
                if events:
                    rows.append(parse_session(sid, events, date))
        print(f"  {os.path.basename(fp):32} sessions={len(rows)-n0}")
    cols = list(rows[0].keys())
    out = os.path.join(OUT_DIR, "sessions.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    dist = collections.Counter(r["intent"] for r in rows)
    n = len(rows)
    print(f"\nTOTAL real sessions: {n:,}  ->  {out}")
    print("Intent distribution (ATT&CK-aligned, from observed behavior):")
    for k, v in dist.most_common():
        print(f"  {k:18} {v:7,}  ({100*v/n:5.1f}%)")
    eng = sum(v for k, v in dist.items() if k != "bruteforce")
    print(f"Engaged (non-bruteforce): {eng:,} ({100*eng/n:.1f}%)")
    print(f"Sessions w/ creds captured: {sum(1 for r in rows if r['n_distinct_creds']>0):,}")
    print(f"Distinct sensors: {len({r['sensor'] for r in rows})}  | dates: {sorted({r['date'] for r in rows})}")


if __name__ == "__main__":
    main()
