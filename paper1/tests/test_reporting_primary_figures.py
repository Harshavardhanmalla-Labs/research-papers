"""Paper-figure generation tests (Phase 17)."""

from __future__ import annotations

from pathlib import Path

from paper1.reporting.primary_figures import generate_all_figures
from paper1.reporting.report_bundle import load_frozen_primary_results

_EXPECTED_FIGURES = {
    "fig_ehd_by_strategy",
    "fig_fraction_of_oracle",
    "fig_relative_to_epss",
    "fig_ehd_distribution_selected",
    "fig_proposed_vs_epss_by_seed",
}


def test_generate_all_figures_writes_png_and_pdf(tiny_frozen_dir, tmp_path):
    frozen = load_frozen_primary_results(tiny_frozen_dir)
    out = tmp_path / "figures"
    written = generate_all_figures(frozen, out)
    assert set(written) == _EXPECTED_FIGURES
    for name, paths in written.items():
        assert len(paths) == 2, name
        png = next(p for p in paths if p.endswith(".png"))
        pdf = next(p for p in paths if p.endswith(".pdf"))
        assert Path(png).exists() and Path(png).stat().st_size > 0, f"{name} png empty"
        assert Path(pdf).exists() and Path(pdf).stat().st_size > 0, f"{name} pdf empty"


def test_png_files_have_png_signature(tiny_frozen_dir, tmp_path):
    frozen = load_frozen_primary_results(tiny_frozen_dir)
    written = generate_all_figures(frozen, tmp_path / "figures")
    for paths in written.values():
        png = next(p for p in paths if p.endswith(".png"))
        with open(png, "rb") as fh:
            assert fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_no_seaborn_imported_by_reporting():
    # Static guard: no reporting module may IMPORT seaborn (the word may
    # appear in a docstring saying "no seaborn", which is fine).
    for p in Path("src/paper1/reporting").glob("*.py"):
        for line in p.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            assert not stripped.startswith("import seaborn"), p
            assert not stripped.startswith("from seaborn"), p
    # And seaborn must not be loaded as a side effect of importing the package.
    import sys

    import paper1.reporting  # noqa: F401

    assert "seaborn" not in sys.modules


def test_figures_use_agg_backend():
    import matplotlib

    # Importing the figures module forces the Agg (headless) backend.
    import paper1.reporting.primary_figures  # noqa: F401

    assert matplotlib.get_backend().lower() == "agg"
