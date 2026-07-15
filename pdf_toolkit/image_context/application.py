"""image context — application use cases.

`recompress_to_slice` is the single home for the per-image decision:
  cap effective DPI -> resample -> binary-search encoder quality under a byte slice,
  enforcing the QualityFloor. Both the PyMuPDF and pikepdf PDF compressors call this,
  so the algorithm lives in exactly one place (ubiquitous language: TargetSizeSearch).
"""
from __future__ import annotations

from dataclasses import dataclass

from pdf_toolkit.image_context.ports import ImageCodec, QualityMeter
from pdf_toolkit.pdf_context.domain import CompressionTarget, ImageKind, ResampleFilter
from pdf_toolkit.pdf_context.services import TargetSizeSearch
from pdf_toolkit.shared_kernel import EffectiveDpi, PerceptualScore


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
    quality = chosen[0] if chosen else target.quality_range[0]

    data = codec.encode(resized, fmt, quality)
    score = meter.score(original, data)
    return RecompressOutcome(
        data=data, new_width=new_w, new_height=new_h,
        dpi_used=int(effective_dpi.value * scale), quality_used=quality,
        score=score, codec_fmt=fmt,
    )
