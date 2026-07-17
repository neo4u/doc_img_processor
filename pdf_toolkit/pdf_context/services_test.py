"""Pure domain services: BudgetDecomposition + TargetSizeSearch (W4, LLD §Tests)."""

from __future__ import annotations

import pytest

from pdf_toolkit.pdf_context.domain import Codec, DocumentCensus, EmbeddedImage
from pdf_toolkit.pdf_context.services import BudgetDecomposition
from pdf_toolkit.shared_kernel import (
    EffectiveDpi,
    ImageKind,
    MediaFile,
    Metric,
    PerceptualScore,
    QualityFloor,
    TargetSizeSearch,
)


def _img(xref: int, area: float) -> EmbeddedImage:
    return EmbeddedImage(
        xref=xref,
        page_index=0,
        width=1000,
        height=1000,
        kind=ImageKind.COLOR,
        codec=Codec.JPEG,
        effective_dpi=EffectiveDpi(pixels=1000, rendered_inches=8.5),
        rendered_area_sqin=area,
    )


def _census(images, tmp_path) -> DocumentCensus:
    f = tmp_path / "x.pdf"
    f.write_bytes(b"%PDF-1.4 stub")
    return DocumentCensus(file=MediaFile.of(f), page_count=1, images=images, non_image_bytes=0)


class TestBudgetDecomposition:
    def test_allocation_proportional_to_rendered_area(self, tmp_path):
        census = _census([_img(1, 75.0), _img(2, 25.0)], tmp_path)
        slices = BudgetDecomposition.allocate(census, 100_000)
        assert slices[1] == 75_000
        assert slices[2] == 25_000

    def test_every_image_gets_at_least_one_byte(self, tmp_path):
        census = _census([_img(1, 1e9), _img(2, 1e-9)], tmp_path)
        slices = BudgetDecomposition.allocate(census, 1000)
        assert slices[2] >= 1  # max(1, …) guard

    def test_empty_census_yields_empty_allocation(self, tmp_path):
        assert BudgetDecomposition.allocate(_census([], tmp_path), 1000) == {}


class TestTargetSizeSearch:
    """encode(q) = (q*100 bytes, score q/100) — perfectly monotonic fake encoder."""

    @staticmethod
    def _encode(q: int) -> tuple[int, PerceptualScore]:
        return q * 100, PerceptualScore(Metric.SSIM, q / 100)

    def test_finds_largest_quality_that_fits(self):
        search = TargetSizeSearch((20, 95), QualityFloor(Metric.SSIM, 0.0))
        best = search.best_quality(8000, self._encode)
        assert best is not None
        assert 75 <= best[0] <= 80  # 80*100 = 8000 fits; converges just under

    def test_floor_rejection_returns_none(self):
        # Only q<=30 fits 3000 B, but the floor needs score >= 0.60 (q>=60): impossible.
        search = TargetSizeSearch((20, 95), QualityFloor(Metric.SSIM, 0.60))
        assert search.best_quality(3000, self._encode) is None

    def test_probe_count_is_logarithmic(self):
        calls = []

        def counting(q: int):
            calls.append(q)
            return self._encode(q)

        TargetSizeSearch((20, 95), QualityFloor(Metric.SSIM, 0.0)).best_quality(5000, counting)
        assert len(calls) <= 8  # ~log2(75), never a linear sweep


def test_bitonal_resamples_nearest_hard_rule_2():
    """Hard rule #2 (named test): bitonal must not be interpolated into gray."""
    from pdf_toolkit.shared_kernel import ResampleFilter

    assert _img(1, 1.0).resample_filter() is ResampleFilter.LANCZOS  # contone
    bitonal = EmbeddedImage(
        xref=2,
        page_index=0,
        width=100,
        height=100,
        kind=ImageKind.BITONAL,
        codec=Codec.CCITT_G4,
        effective_dpi=EffectiveDpi(pixels=100, rendered_inches=1),
        rendered_area_sqin=1.0,
    )
    assert bitonal.resample_filter() is ResampleFilter.NEAREST


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
