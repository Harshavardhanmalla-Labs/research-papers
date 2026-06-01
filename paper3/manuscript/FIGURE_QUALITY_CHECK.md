# HygieneBench — Figure Quality Check

**Date:** 2026-05-28
**Figures directory:** `paper3/manuscript/figures/`
**Target venue:** ACM CCS AISec Workshop (ACM two-column format)

ACM camera-ready requirements: vector (PDF/EPS) strongly preferred; raster minimum 300 DPI at final print size.

---

## Figure inventory

### Figure 1 — AP Heatmap (method × task, condition-averaged)

| Property | PNG | PDF |
|---|---|---|
| Filename | `fig1_ap_heatmap.png` | `fig1_ap_heatmap.pdf` |
| Dimensions (px) | 1253 × 577 | vector |
| File size | 79,343 bytes | 27,208 bytes |
| DPI (embedded pHYs) | **150 DPI** | N/A (vector) |
| Format | Raster PNG | Vector PDF |
| Acceptable for submission | **Use PDF** | ✅ Yes |

**Assessment:** PDF is vector — preferred for ACM submission. PNG at 150 DPI is below the 300 DPI threshold and should NOT be used as the submission figure. Use `fig1_ap_heatmap.pdf`.

**Required action:** Submit PDF. PNG regeneration optional (see note below).

---

### Figure 2 — Failure-Flag Heatmap (method × task)

| Property | PNG | PDF |
|---|---|---|
| Filename | `fig2_failure_heatmap.png` | `fig2_failure_heatmap.pdf` |
| Dimensions (px) | 1254 × 583 | vector |
| File size | 64,884 bytes | 25,538 bytes |
| DPI (embedded pHYs) | **150 DPI** | N/A (vector) |
| Format | Raster PNG | Vector PDF |
| Acceptable for submission | **Use PDF** | ✅ Yes |

**Visual inspection result (2026-05-31):** Fig2 PDF was rendered and inspected. Findings:

- **Title:** "Failure-Flag Rate by Method x Task" with subtitle "(fraction of conditions where ML does not beat rule by delta=0.05)" — both lines render clearly and are fully readable.
- **Row labels (method names):** M1 Rule, M5 OCSVM, M4 LOF, M3 IForest, M6 Linear-AE, M7 Z-score, M8 Graph-IF, M2 Hybrid — all fully legible, no truncation, adequately sized.
- **Column labels (task names):** T1 through T7 at the bottom — all legible.
- **Cell percentage annotations:** All numeric labels (100%, 13%, 0%, 33%, 73%, 20%, 87%, 93%) are clearly printed inside each cell with sufficient contrast. White text on dark-red cells and dark text on green/orange cells both render legibly. The "N/A" labels in M8 Graph-IF x T4 and T5 cells are printed in gray on a white/light background and are readable.
- **Colorbar:** Present on the right side, labeled "Failure Rate", with tick marks at 0.0, 0.2, 0.4, 0.6, 0.8, 1.0. Color gradient from dark green (0.0) through orange to dark red (1.0) is clear and interpretable. Colorbar label is readable.
- **Color scale legibility:** The diverging green-to-red scheme communicates failure rates intuitively. The 0% cell (M5 OCSVM x T5) is rendered in dark green, correctly indicating zero failure rate — the key positive result for T5.
- **M1 Rule row:** Correctly shows dashes ("—") across all tasks, indicating M1 is the reference baseline with no failure-flag computation.
- **Two-column ACM fit (~3.25 inches wide):** The figure has a wide landscape aspect ratio (approximately 2.2:1). At 3.25 inches wide (single column), it would render at roughly 1.5 inches tall — row labels and percentage annotations may become borderline small but remain legible because the font sizes are generous. At 6.5 inches wide (two-column span with `\begin{figure*}`), all elements are comfortably readable. **Recommendation: use `\begin{figure*}` for this figure in the ACM LaTeX scaffold to span both columns.**
- **No mispositioned annotations observed:** The matplotlib "posx and posy should be finite" warning from generation did not produce any visible annotation errors in the rendered PDF. All percentage labels appear centered within their respective cells.

**Overall assessment:** PASS — fig2_failure_heatmap.pdf is acceptable for submission as-is.

**Required action:** In `submission/acm/sections/results.tex`, confirm this figure uses `\begin{figure*}` (two-column span) rather than single-column `\begin{figure}`. No regeneration required.

---

### Figure 3 — AP Distribution by Condition (boxplot)

| Property | PNG | PDF |
|---|---|---|
| Filename | `fig3_ap_by_condition.png` | `fig3_ap_by_condition.pdf` |
| Dimensions (px) | 1482 × 652 | vector |
| File size | 45,679 bytes | 18,421 bytes |
| DPI (embedded pHYs) | **150 DPI** | N/A (vector) |
| Format | Raster PNG | Vector PDF |
| Acceptable for submission | **Use PDF** | ✅ Yes |

**Assessment:** PDF vector — acceptable. Dimensions suggest a wider figure; verify it fits within a single column or spans two columns as intended in the ACM template.

**Required action:** Submit PDF. Verify column width fit in LaTeX layout.

---

### Figure 4 — T2 and T5 ML Gain Bar Chart

| Property | PNG | PDF |
|---|---|---|
| Filename | `fig4_t2_t5_ml_gain.png` | `fig4_t2_t5_ml_gain.pdf` |
| Dimensions (px) | 1635 × 661 | vector |
| File size | 62,197 bytes | 19,228 bytes |
| DPI (embedded pHYs) | **150 DPI** | N/A (vector) |
| Format | Raster PNG | Vector PDF |
| Acceptable for submission | **Use PDF** | ✅ Yes |

**Assessment:** PDF vector — acceptable. This is the widest figure (1635 px PNG equivalent) — confirm it renders clearly as a two-column-spanning figure in LaTeX.

**Required action:** Submit PDF. Recommend `\begin{figure*}...\end{figure*}` in LaTeX for two-column span.

---

## Summary

| Figure | PDF acceptable | PNG acceptable | Action needed |
|---|---|---|---|
| fig1_ap_heatmap | ✅ Yes | ⚠️ 150 DPI — do not use | Use PDF |
| fig2_failure_heatmap | ✅ Yes (inspect annotations) | ⚠️ 150 DPI — do not use | Inspect fig2 PDF annotations before submission |
| fig3_ap_by_condition | ✅ Yes | ⚠️ 150 DPI — do not use | Verify column fit in LaTeX |
| fig4_t2_t5_ml_gain | ✅ Yes | ⚠️ 150 DPI — do not use | Use `figure*` env in LaTeX |

**All four PDFs are vector and acceptable for ACM submission. PNGs are 150 DPI and should not be used as submission figures.**

---

## PNG regeneration (optional, for preprint/arXiv)

If 300 DPI PNGs are needed for arXiv or preprint upload, regenerate by adding `dpi=300` to the `savefig()` calls in the figure generation script. The script is at: `src/` (check for `generate_figures.py` or equivalent). This does not affect the paper submission which uses PDFs.

---

*Internal document — do not include in artifact release.*
