FIGURES DIRECTORY — HygieneBench ACM Submission
================================================

This directory must contain the figure PDFs before compiling main.tex.

Copy or symlink the following files from:
  paper3/manuscript/figures/

Required files:
  fig1_ap_heatmap.pdf
  fig2_failure_heatmap.pdf      [INSPECT ANNOTATIONS — see FIGURE_QUALITY_CHECK.md]
  fig3_ap_by_condition.pdf
  fig4_t2_t5_ml_gain.pdf

Copy command (run from paper3/ root):
  cp manuscript/figures/fig1_ap_heatmap.pdf submission/acm/figures/
  cp manuscript/figures/fig2_failure_heatmap.pdf submission/acm/figures/
  cp manuscript/figures/fig3_ap_by_condition.pdf submission/acm/figures/
  cp manuscript/figures/fig4_t2_t5_ml_gain.pdf submission/acm/figures/

DO NOT use PNG files for the LaTeX submission — all four PDFs are vector and
preferred by ACM. PNGs are 150 DPI and below the 300 DPI print threshold.

See FIGURE_QUALITY_CHECK.md for full quality assessment.
