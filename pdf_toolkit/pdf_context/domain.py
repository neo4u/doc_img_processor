"""pdf context — domain layer. Pure: no third-party imports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pdf_toolkit.shared_kernel import (
    EffectiveDpi,
    ImageKind,
    MediaFile,
    PerceptualScore,
    ResampleFilter,
)


class Codec(str, Enum):
    JPEG = "jpeg"  # DCTDecode
    CCITT_G4 = "ccitt_g4"  # CCITTFaxDecode
    FLATE = "flate"
    PNG = "png"
    JBIG2 = "jbig2"
    RAW = "raw"


@dataclass(frozen=True)
class EmbeddedImage:
    """One raster image on a page."""

    xref: int
    page_index: int  # 0-based
    width: int
    height: int
    kind: ImageKind
    codec: Codec
    effective_dpi: EffectiveDpi
    rendered_area_sqin: float

    def resample_filter(self) -> ResampleFilter:
        # Hard rule #2: bitonal must not be interpolated into gray.
        return ResampleFilter.NEAREST if self.kind is ImageKind.BITONAL else ResampleFilter.LANCZOS


@dataclass(frozen=True)
class DocumentCensus:
    """Output of inspect: what's inside a PDF."""

    file: MediaFile
    page_count: int
    images: list[EmbeddedImage]
    non_image_bytes: int

    @property
    def image_bytes_fraction(self) -> float:
        total = self.file.size_bytes
        return (total - self.non_image_bytes) / total if total else 0.0

    @property
    def total_rendered_area(self) -> float:
        return sum(i.rendered_area_sqin for i in self.images) or 1.0


@dataclass(frozen=True)
class CompressionResult:
    output: MediaFile
    engine: str
    before_bytes: int
    after_bytes: int
    dpi_used: int
    quality_used: int
    score: PerceptualScore | None
    elapsed_ms: int
    escalated: bool = False  # true if Ghostscript fallback fired

    @property
    def ratio(self) -> float:
        return self.after_bytes / self.before_bytes if self.before_bytes else 1.0

    @property
    def saved_pct(self) -> float:
        return 100 * (1 - self.ratio)


# --- Domain events -----------------------------------------------------------
