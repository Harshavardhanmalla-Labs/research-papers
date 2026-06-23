"""Reporting layer (Phase 17): paper-ready tables and figures.

Tables and figures are generated *only* from the frozen primary artifact
(after its freeze manifest verifies). This layer performs no interpretation
and asserts no paper claims -- it renders the frozen numbers reproducibly.
EHD is treated consistently as lower-is-better.
"""

from paper1.reporting.primary_figures import generate_all_figures
from paper1.reporting.primary_tables import generate_all_tables, write_table
from paper1.reporting.report_bundle import (
    generate_primary_report_bundle,
    load_frozen_primary_results,
)

__all__ = [
    "generate_all_figures",
    "generate_all_tables",
    "generate_primary_report_bundle",
    "load_frozen_primary_results",
    "write_table",
]
