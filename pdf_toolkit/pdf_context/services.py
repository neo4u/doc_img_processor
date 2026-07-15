"""pdf context — domain services. Pure orchestration; no library imports.

TargetSizeSearch: monotonic binary search over encoder quality (and dimensions).
BudgetDecomposition: split a byte budget across images by rendered area.
"""
from __future__ import annotations

from typing import Callable

from pdf_toolkit.pdf_context.domain import DocumentCensus, EmbeddedImage
from pdf_toolkit.shared_kernel import ByteBudget, PerceptualScore, QualityFloor


class BudgetDecomposition:
    """Allocate a PDF's image byte budget across images ∝ rendered area."""

    @staticmethod
    def allocate(census: DocumentCensus, image_budget_bytes: int) -> dict[int, int]:
        total_area = census.total_rendered_area
        return {
            img.xref: max(1, int(image_budget_bytes * img.rendered_area_sqin / total_area))
            for img in census.images
        }


class TargetSizeSearch:
    """Largest encoder quality whose output fits `slice_bytes`, respecting the floor.

    `encode` maps quality -> (num_bytes, PerceptualScore). Size must be monotonic
    non-decreasing in quality (true for JPEG/WebP). ~7 probes for a 20..95 range.
    """

    def __init__(self, quality_range: tuple[int, int], floor: QualityFloor) -> None:
        self._lo, self._hi = quality_range
        self._floor = floor

    def best_quality(
        self,
        slice_bytes: int,
        encode: Callable[[int], tuple[int, PerceptualScore]],
    ) -> tuple[int, PerceptualScore] | None:
        lo, hi = self._lo, self._hi
        best: tuple[int, PerceptualScore] | None = None
        while hi - lo > 1:
            q = (lo + hi) // 2
            size, score = encode(q)
            fits = size <= slice_bytes
            if fits:
                if self._floor.accepts(score):
                    best = (q, score)
                lo = q            # try higher quality
            else:
                hi = q            # too big, lower quality
        return best
