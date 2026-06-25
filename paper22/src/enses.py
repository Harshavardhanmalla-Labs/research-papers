#!/usr/bin/env python3
"""ENSES — Explainable Neuro-Symbolic Expert System for cyber-risk prioritization.

Real public data (FIRST.org EPSS + CISA KEV, 203,174 CVEs / 1,612 exploited) joined
to a transparent smart-city / IIoT / healthcare asset estate. A knowledge graph
(CVE -> CWE -> weakness-class -> ATT&CK-tactic -> asset-class) plus inference rules
form the symbolic tier; nomic-embed-text embeddings of real CVE descriptions vs
asset-class profiles form the neural (RAG) tier; an additive, glass-box inference
engine fuses {EPSS, symbolic applicability, neural relevance, asset criticality}.

Evaluated against an exploitation-and-relevance-weighted ground truth with
asset-criticality weighting; baselines include the prior ensemble (XGBoost),
EPSS-only, KEV-first, and random; ablations remove each ENSES tier.
Frozen -> paper22/results/primary_v1/.
"""
from __future__ import annotations
import os, json, re, time, hashlib, warnings, urllib.request
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.metrics import ndcg_score
from xgboost import XGBRegressor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "results", "primary_v1"); os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(HERE, "data"); os.makedirs(CACHE, exist_ok=True)
RNG = np.random.default_rng(20260625)

# ── Smart-city / IIoT / healthcare asset estate (transparent; DP on aggregates) ──
ASSET_CLASSES = {
    "smart_grid_controller": "industrial control system and programmable logic controller managing electricity distribution, SCADA, energy substation automation",
    "intelligent_transport": "traffic signal controller, connected roadside unit, transport management and mobility edge gateway",
    "connected_medical":     "connected medical device, hospital patient monitor, infusion and imaging system on a clinical network",
    "water_utility_iiot":    "water treatment and utility industrial IoT sensor, pump and valve actuator, environmental telemetry",
    "building_automation":   "building automation controller, HVAC, access control and elevator management on a facilities network",
    "edge_compute_gateway":  "edge compute gateway, container host, message broker and API gateway aggregating IoT device telemetry",
}
CRIT_W = {1: 1.0, 2: 2.0, 3: 4.0, 4: 8.0}  # criticality-tier weights

# Curated, defensible product/keyword -> asset-class applicability (symbolic KG layer).
CLASS_KEYWORDS = {
    "smart_grid_controller": ["scada","plc","ics","modbus","iec 61850","substation","siemens","schneider","rockwell","energy","power","grid","controller"],
    "intelligent_transport": ["traffic","transport","roadside","telematics","mobility","railway","automotive","vehicle","gps"],
    "connected_medical":     ["medical","health","patient","hospital","infusion","imaging","dicom","hl7","clinical","philips","ge healthcare"],
    "water_utility_iiot":    ["water","utility","pump","valve","wastewater","sensor","telemetry","environmental","iiot","industrial"],
    "building_automation":   ["building","hvac","bacnet","access control","elevator","facility","camera","surveillance"],
    "edge_compute_gateway":  ["gateway","broker","mqtt","api","container","docker","kubernetes","edge","router","linux","apache","nginx"],
}
# CWE -> weakness class -> indicative ATT&CK tactic (curated real mappings)
CWE_CLASS = {
    "CWE-79":"injection","CWE-89":"injection","CWE-78":"injection","CWE-94":"injection","CWE-77":"injection",
    "CWE-787":"memory","CWE-125":"memory","CWE-119":"memory","CWE-416":"memory","CWE-190":"memory",
    "CWE-22":"path","CWE-434":"path","CWE-98":"path",
    "CWE-287":"authn","CWE-306":"authn","CWE-862":"authz","CWE-863":"authz","CWE-269":"authz","CWE-918":"ssrf",
    "CWE-352":"web","CWE-200":"infoleak","CWE-502":"deser","CWE-20":"input","CWE-400":"dos","CWE-noinfo":"other",
}
CLASS_TACTIC = {"injection":"execution","memory":"execution","path":"persistence","authn":"initial-access",
    "authz":"privilege-escalation","ssrf":"discovery","web":"execution","infoleak":"collection",
    "deser":"execution","input":"execution","dos":"impact","other":"other"}


def ollama_embed(texts, model="nomic-embed-text"):
    out = []
    for t in texts:
        body = json.dumps({"model": model, "prompt": t}).encode()
        req = urllib.request.Request("http://localhost:11434/api/embeddings", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            out.append(json.loads(r.read())["embedding"])
    return np.array(out, dtype=np.float32)


def load_data():
    corpus = pd.read_csv(os.path.join(ROOT, "real_data/processed/cve_corpus_for_sampling.csv"))
    corpus["in_kev"] = corpus["in_kev"].astype(str).str.lower().eq("true")
    kev = json.load(open(os.path.join(ROOT, "real_data/raw/kev.json")))["vulnerabilities"]
    meta = {}
    for v in kev:
        cwes = v.get("cwes") or ["CWE-noinfo"]
        meta[v["cveID"]] = {"desc": v.get("shortDescription", ""), "product": v.get("product", ""),
                            "vendor": v.get("vendorProject", ""),
                            "ransom": v.get("knownRansomwareCampaignUse", "Unknown").lower() == "known",
                            "cwe": cwes[0]}
    return corpus, meta


def applicability_symbolic(text):
    """KG layer: product/keyword -> per-asset-class applicability in [0,1]."""
    t = text.lower()
    a = {}
    for cls, kws in CLASS_KEYWORDS.items():
        hits = sum(1 for k in kws if k in t)
        a[cls] = min(1.0, 0.34 * hits)
    return a


def cosine(a, B):
    a = a / (np.linalg.norm(a) + 1e-9)
    Bn = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-9)
    return Bn @ a


def build_features(corpus, meta):
    """Per-CVE features + neural relevance to each asset class (cached embeddings)."""
    classes = list(ASSET_CLASSES)
    # asset-class profile embeddings
    prof_emb = ollama_embed([ASSET_CLASSES[c] for c in classes])
    # embed KEV descriptions (cache)
    kev_ids = [c for c in corpus["cve"] if c in meta and meta[c]["desc"]]
    cpath = os.path.join(CACHE, "kev_emb.npz")
    if os.path.exists(cpath):
        z = np.load(cpath, allow_pickle=True); emb = z["emb"]; ids = list(z["ids"])
    else:
        ids = kev_ids
        print(f"embedding {len(ids)} KEV descriptions via nomic-embed-text…")
        emb = ollama_embed([meta[c]["desc"] for c in ids])
        np.savez(cpath, emb=emb, ids=np.array(ids))
    id2row = {c: i for i, c in enumerate(ids)}
    # neural relevance per (cve, class) for described CVEs
    neural = {}
    for c in ids:
        neural[c] = np.clip(cosine(emb[id2row[c]], prof_emb), 0, None)  # len = #classes
    return classes, prof_emb, neural


def cve_table(corpus, meta, classes, neural):
    rows = []
    for cve, epss, kev in corpus[["cve", "epss", "in_kev"]].itertuples(index=False):
        m = meta.get(cve)
        sym = applicability_symbolic((m["product"] + " " + m["vendor"] + " " + m["desc"]) if m else "")
        sym_v = np.array([sym[c] for c in classes])
        neu_v = neural.get(cve, np.zeros(len(classes)))
        rows.append((cve, float(epss), bool(kev), bool(m["ransom"]) if m else False,
                     (m["cwe"] if m else "CWE-noinfo"), sym_v, neu_v))
    return rows
