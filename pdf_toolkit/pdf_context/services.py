"""pdf context — domain services. Pure orchestration; no library imports.

BudgetDecomposition: split a byte budget across images by rendered area.
(TargetSizeSearch moved to shared_kernel 2026-07-15 — one home, W2.)
"""

from __future__ import annotations

from pdf_toolkit.pdf_context.domain import DocumentCensus


class BudgetDecomposition:
    """Allocate a PDF's image byte budget across images ∝ rendered area."""

    @staticmethod
    def allocate(census: DocumentCensus, image_budget_bytes: int) -> dict[int, int]:
        total_area = census.total_rendered_area
        return {
            img.xref: max(1, int(image_budget_bytes * img.rendered_area_sqin / total_area))
            for img in census.images
        }
