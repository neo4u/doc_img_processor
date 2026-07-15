"""pdf context — domain layer. Pure: no third-party imports."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pdf_toolkit.shared_kernel import (
    ByteBudget,
    EffectiveDpi,
    MediaFile,
    PerceptualScore,
    QualityFloor,
)


class ImageKind(str, Enum):
    BITONAL = "bitonal"      # 1-bit black/white — CCITT/Group4 territory
    GRAYSCALE = "grayscale"
    COLOR = "color"

    @property
    def is_contone(self) -> bool:
        return self is not ImageKind.BITONAL


class Codec(str, Enum):
    JPEG = "jpeg"            # DCTDecode
    CCITT_G4 = "ccitt_g4"    # CCITTFaxDecode
    FLATE = "flate"
    PNG = "png"
    JBIG2 = "jbig2"
    RAW = "raw"


class ResampleFilter(str, Enum):
    NEAREST = "nearest"      # bitonal only
    LANCZOS = "lanczos"      # contone


@dataclass(frozen=True)
class PageRange:
    """1-indexed, inclusive."""
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError(f"start must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) < start ({self.start})")

    @classmethod
    def single(cls, page: int) -> "PageRange":
        return cls(page, page)

    @classmethod
    def from_pages(cls, pages: list[int]) -> "PageRange":
        return cls(min(pages), max(pages))

    @property
    def page_numbers(self) -> list[int]:
        return list(range(self.start, self.end + 1))

    def __len__(self) -> int:
        return self.end - self.start + 1

    def __str__(self) -> str:
        return f"p{self.start}" if len(self) == 1 else f"p{self.start}-{self.end}"


@dataclass(frozen=True)
class SplitSpec:
    name: str
    page_range: PageRange


@dataclass(frozen=True)
class EmbeddedImage:
    """One raster image on a page."""
    xref: int
    page_index: int          # 0-based
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
class CompressionTarget:
    budget: ByteBudget
    quality_floor: QualityFloor = field(default_factory=QualityFloor)
    dpi_cap: int = 200            # contone cap: 150 screen / 225 print; 200 = balanced
    dpi_range: tuple[int, int] = (72, 300)
    quality_range: tuple[int, int] = (20, 95)   # JPEG encoder quality search bounds


@dataclass(frozen=True)
class CompressionRecipe:
    """Per-image decision produced by the domain services."""
    xref: int
    target_dpi: int
    quality: int
    codec: Codec
    resample: ResampleFilter


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
    escalated: bool = False       # true if Ghostscript fallback fired

    @property
    def ratio(self) -> float:
        return self.after_bytes / self.before_bytes if self.before_bytes else 1.0

    @property
    def saved_pct(self) -> float:
        return 100 * (1 - self.ratio)


# --- Domain events -----------------------------------------------------------
@dataclass(frozen=True)
class CompressionAttempted:
    file: str
    engine: str
    after_bytes: int


@dataclass(frozen=True)
class BudgetMissed:
    file: str
    engine: str
    after_bytes: int
    ceiling: int


@dataclass(frozen=True)
class QualityFloorViolated:
    file: str
    score: PerceptualScore
    floor: QualityFloor
