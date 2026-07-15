"""image context — application use cases.

`recompress_to_slice` is the single home for the per-image decision:
  cap effective DPI -> resample -> binary-search encoder quality under a byte slice,
  enforcing the QualityFloor. Both the PyMuPDF and pikepdf PDF compressors call this,
  so the algorithm lives in exactly one place (ubiquitous language: TargetSizeSearch).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pdf_toolkit.image_context.ports import ImageCodec, LosslessOptimizer, QualityMeter
from pdf_toolkit.shared_kernel import (
    CompressionTarget,
    EffectiveDpi,
    ImageKind,
    LosslessOutcome,
    MediaFile,
    PerceptualScore,
    ResampleFilter,
    TargetSizeSearch,
)


@dataclass(frozen=True)
class RecompressOutcome:
    data: bytes
    new_width: int
    new_height: int
    dpi_used: int
    quality_used: int
    score: PerceptualScore
    codec_fmt: str


def recompress_to_slice(
    *,
    original: bytes,
    kind: ImageKind,
    width: int,
    height: int,
    effective_dpi: EffectiveDpi,
    target: CompressionTarget,
    slice_bytes: int,
    codec: ImageCodec,
    meter: QualityMeter,
) -> RecompressOutcome:
    resample = ResampleFilter.NEAREST if kind is ImageKind.BITONAL else ResampleFilter.LANCZOS
    fmt = "TIFF" if kind is ImageKind.BITONAL else "JPEG"

    scale = effective_dpi.scale_to(target.dpi_cap)
    new_w = max(1, int(width * scale))
    new_h = max(1, int(height * scale))

    base = codec.decode(original)
    resized = codec.resize(base, new_w, new_h, resample)

    search = TargetSizeSearch(target.quality_range, target.quality_floor)

    def encode(q: int) -> tuple[int, PerceptualScore]:
        buf = codec.encode(resized, fmt, q)
        return len(buf), meter.score(original, buf)

    chosen = search.best_quality(slice_bytes, encode)
    if chosen is not None:
        quality = chosen[0]
    else:
        # Nothing fit the slice at an acceptable score. The floor is the domain
        # invariant (hard rule #4) — never sacrifice it for the budget: pick the
        # LOWEST quality the floor accepts (smallest acceptable file) and let the
        # caller's budget check trigger escalation. Never quality_range[0] blindly.
        quality = _lowest_floor_quality(target, encode)

    data = codec.encode(resized, fmt, quality)
    score = meter.score(original, data)
    return RecompressOutcome(
        data=data,
        new_width=new_w,
        new_height=new_h,
        dpi_used=int(effective_dpi.value * scale),
        quality_used=quality,
        score=score,
        codec_fmt=fmt,
    )


def _lowest_floor_quality(
    target: CompressionTarget,
    encode: Callable[[int], tuple[int, PerceptualScore]],
) -> int:
    """Coarse upward walk: first quality the floor accepts; ceiling of range if none."""
    lo, hi = target.quality_range
    for q in range(lo, hi, 10):
        _, score = encode(q)
        if target.quality_floor.accepts(score):
            return q
    return hi


@dataclass
class CompressImageLossless:
    """Shrink a JPEG/PNG with bit-exact pixels. Hard rule #1: never emit larger."""

    optimizer: LosslessOptimizer

    def __call__(self, input_path: str | Path, out_path: str | Path) -> LosslessOutcome:
        source = MediaFile.of(input_path)
        if not source.exists:
            raise FileNotFoundError(f"file not found: {source.path}")
        original = source.path.read_bytes()
        optimized = self.optimizer.optimize(original, source.path.suffix)

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if len(optimized) >= len(original):  # hard rule #1
            out.write_bytes(original)
            return LosslessOutcome(MediaFile.of(out), len(original), len(original), changed=False)
        out.write_bytes(optimized)
        return LosslessOutcome(MediaFile.of(out), len(original), len(optimized), changed=True)
