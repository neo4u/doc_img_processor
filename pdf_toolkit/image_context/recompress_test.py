"""recompress_to_slice — floor semantics (hard rule #4 regression, REVIEW/RESEARCH 2026-07-15).

Uses fake codec/meter so the search behavior is tested pure, no Pillow needed.
"""

from __future__ import annotations

from pdf_toolkit.image_context.application import recompress_to_slice
from pdf_toolkit.image_context.ports import ImageCodec, QualityMeter
from pdf_toolkit.shared_kernel import (
    ByteBudget,
    CompressionTarget,
    EffectiveDpi,
    ImageKind,
    Metric,
    PerceptualScore,
    QualityFloor,
    ResampleFilter,
)


class FakeCodec(ImageCodec):
    """Encodes to `quality * 100` bytes — perfectly monotonic."""

    def decode(self, data: bytes):
        return data

    def resize(self, img, width: int, height: int, resample: ResampleFilter):
        return img

    def encode(self, img, fmt: str, quality: int) -> bytes:
        return b"x" * (quality * 100)


class SteppedMeter(QualityMeter):
    """Score = quality/100 (recovered from candidate size) — floor accepts q >= threshold*100."""

    def score(self, original: bytes, candidate: bytes) -> PerceptualScore:
        return PerceptualScore(Metric.SSIM, (len(candidate) // 100) / 100)


def _run(slice_bytes: int, floor: float) -> tuple[int, float]:
    target = CompressionTarget(
        budget=ByteBudget.kb(1000),
        quality_floor=QualityFloor(Metric.SSIM, floor),
        quality_range=(20, 95),
    )
    out = recompress_to_slice(
        original=b"orig",
        kind=ImageKind.COLOR,
        width=1000,
        height=1000,
        effective_dpi=EffectiveDpi(pixels=1000, rendered_inches=10),
        target=target,
        slice_bytes=slice_bytes,
        codec=FakeCodec(),
        meter=SteppedMeter(),
    )
    return out.quality_used, out.score.value


def test_search_picks_largest_quality_that_fits_and_passes_floor():
    q, score = _run(slice_bytes=8000, floor=0.30)  # q80 fits (8000 B), passes floor
    assert 75 <= q <= 80
    assert score >= 0.30


def test_floor_miss_never_falls_back_to_worst_quality():
    # Slice so tight nothing passing the floor fits: floor needs q>=60 (6000 B),
    # but the slice is 3000 B. Old bug returned quality_range[0] == 20 — a floor
    # violation as punishment. Fix: lowest quality the floor accepts (60).
    q, score = _run(slice_bytes=3000, floor=0.60)
    assert q >= 60, f"floor sacrificed: got q={q}"
    assert score >= 0.60  # hard rule #4: result never below the floor


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
