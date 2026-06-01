# Venue CFP Status — Paper 2 (CalibScore / "When Calibration Fails")

Generated: 2026-05-31

---

## LaTeX Compile Status Note

`submission/cset/main.tex` currently uses:

```latex
\documentclass[11pt,letterpaper]{article}
```

with a conservative, template-agnostic preamble (`geometry`, `booktabs`, `hyperref`, `cite`).

**What must change before CSET submission:**
- Replace `\documentclass[11pt,letterpaper]{article}` with the IEEE conference class:
  `\documentclass[conference,compsoc]{IEEEtran}`
- Remove `\usepackage[margin=1in]{geometry}` — IEEEtran sets its own margins.
- Remove `\usepackage{cite}` — IEEEtran bundles citation handling; use `\bibliographystyle{IEEEtran}`.
- Confirm `\usepackage{microtype}` is compatible (generally fine with IEEEtran).
- Strip anonymous author stub `\author{Anonymous (submission scaffold)}` — replace with
  a blank `\author{}` or the appropriate double-blind placeholder per the official template.
- Download the current IEEEtran template from IEEE or Overleaf before final submission
  and re-check layout, especially figure/table widths that assume a two-column format.

**For LASER (ACSAC):** LASER has historically used a two-column ACM format
(ACM `sigconf` or `acmart`). Check the current LASER CFP PDF for the exact class.

---

## CSET 2026 — Cyber Security Experimentation and Test Workshop

**Status: CFP NOT YET PUBLISHED as of 2026-05-31**

CSET 2026 has not announced a call for papers or an official website. The most recent
edition is **CSET 2025 (18th)**, co-located with ACSAC 2025 in Honolulu, HI
(December 8, 2025). Based on the CSET 2025 CFP (https://cset25.isi.edu/cfp.html),
the historical pattern for CSET is:

| Parameter         | CSET 2025 (most recent confirmed)                              |
|-------------------|----------------------------------------------------------------|
| Co-location       | ACSAC (December, annually)                                     |
| Page limit        | Short: 4 pp; Long: 8 pp (excl. references and appendices)     |
| Review type       | **Double-blind** (authors must anonymize)                      |
| Template          | IEEE conference — `\documentclass[conference,compsoc]{IEEEtran}` |
| Submission portal | HotCRP (https://cset25.hotcrp.com/ for 2025 edition)          |
| Proceedings       | Published through IEEE Computer Society                         |
| Paper deadline    | Mid-September (Sep 17 extended in 2025)                        |
| Notification      | Mid-October                                                    |
| Camera-ready      | Mid-November                                                   |

USENIX Security 2026 (August 12-14, Baltimore) does **not** list CSET as an affiliated
workshop. CSET co-locates with ACSAC, not USENIX Security. The USENIX Security 2026
affiliated workshops are GREPSEC VII, WOOT '26, and VehicleSec '26.

**Action required:** Watch https://cset26.isi.edu/ (URL follows established pattern but
not yet live as of 2026-05-31). Subscribe to the csetchairs@gmail.com mailing or check
the ACSAC 2026 workshops page (https://www.acsac.org/2026/workshops/) once it populates.
ACSAC 2026 runs December 7-11, 2026 in Los Angeles, CA.

---

## LASER 2026 — Learning from Authoritative Security Experiment Results

**Status: CFP NOT YET PUBLISHED as of 2026-05-31**

LASER 2026 has not announced a call for papers. The most recent edition is
**LASER 2025**, co-located with ACSAC 2025 (December 8-12, Honolulu, HI).
Based on the LASER@ACSAC 2024 and 2025 CFPs, the historical pattern is:

| Parameter         | LASER 2025 (most recent confirmed; from LASER2025_CFP.pdf)     |
|-------------------|----------------------------------------------------------------|
| Co-location       | ACSAC (December, annually)                                     |
| Page limit        | Typically 6-8 pp (verify in current CFP PDF — details in LASER2025_CFP.pdf are not text-extractable; consistent with prior years) |
| Review type       | Peer-reviewed; historically single-blind (verify with 2026 CFP) |
| Template          | ACM format (two-column); verify exact class in CFP             |
| Proceedings       | ACM Digital Library (ACSAC workshop proceedings)               |
| Focus             | Experimental rigor, reproducibility, negative results          |

**Action required:** Monitor https://www.acsac.org/2026/workshops/ for a LASER 2026
page. ACSAC 2026 runs December 7-11, 2026 in Los Angeles, CA. Workshop proposals for
ACSAC 2026 are currently being solicited.

---

## Recommendations

1. **Primary target (CSET):** The manuscript is formatted as a CSET paper in scope and
   structure. CSET 2025 used an 8-page long-paper limit with IEEE double-blind review.
   Expect similar constraints for CSET 2026. Switch `main.tex` to IEEEtran before final
   submission. Current draft needs page-count verification once reflowed in IEEEtran.

2. **Secondary target (LASER):** LASER welcomes experimental and negative-result papers,
   which aligns with CalibScore's failure-mode framing. Page limit likely 6-8 pp.
   Requires a separate ACM-template branch under `submission/laser/` if pursued.

3. **Neither CFP is live:** Do not submit yet. Re-check venue websites in August-September
   2026, which is when both workshops historically publish their CFPs for December
   co-located deadlines.
