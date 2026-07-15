"""Shared kernel — value objects used across the pdf and image contexts.

Immutable, validated on construction, no third-party imports. These names are the
ubiquitous language; Rust and Go mirror them exactly. See ../../DOMAIN.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Metric(str, Enum):
    SSIM = "ssim"  # higher is better, 0..1
    DSSIM = "dssim"  # lower is better, 0..
    BUTTERAUGLI = "butteraugli"

    @property
    def higher_is_better(self) -> bool:
        return self is Metric.SSIM


@dataclass(frozen=True)
class MediaFile:
    """A file on disk (value object keyed by path)."""

    path: Path

    @classmethod
    def of(cls, path: str | Path) -> MediaFile:
        return cls(path=Path(path))

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def size_bytes(self) -> int:
        return self.path.stat().st_size

    @property
    def size_kb(self) -> int:
        return self.size_bytes // 1000


@dataclass(frozen=True)
class ByteBudget:
    """A target size with tolerance. Default: never over target, no lower bound."""

    target_bytes: int
    over_tolerance: float = 0.0  # fraction the ceiling may exceed target (e.g. 0.05)

    def __post_init__(self) -> None:
        if self.target_bytes <= 0:
            raise ValueError("target_bytes must be positive")
        if self.over_tolerance < 0:
            raise ValueError("over_tolerance must be >= 0")

    @classmethod
    def kb(cls, kb: int, over_tolerance: float = 0.0) -> ByteBudget:
        return cls(target_bytes=kb * 1000, over_tolerance=over_tolerance)

    def ceiling(self) -> int:
        return int(self.target_bytes * (1 + self.over_tolerance))

    def contains(self, n: int) -> bool:
        return n <= self.ceiling()

    def overshoot(self, n: int) -> int:
        return max(0, n - self.ceiling())


@dataclass(frozen=True)
class PerceptualScore:
    metric: Metric
    value: float

    def is_at_least(self, other: PerceptualScore | float) -> bool:
        threshold = other.value if isinstance(other, PerceptualScore) else other
        return self.value >= threshold if self.metric.higher_is_better else self.value <= threshold


@dataclass(frozen=True)
class QualityFloor:
    """A perceptual acceptance threshold. Enforced as a domain invariant."""

    metric: Metric = Metric.SSIM
    threshold: float = 0.90

    def accepts(self, score: PerceptualScore) -> bool:
        if score.metric is not self.metric:
            raise ValueError(f"score metric {score.metric} != floor metric {self.metric}")
        return score.is_at_least(self.threshold)


@dataclass(frozen=True)
class EffectiveDpi:
    """Resolution as actually rendered on the page. From geometry, never metadata."""

    pixels: int
    rendered_inches: float

    def __post_init__(self) -> None:
        if self.rendered_inches <= 0:
            raise ValueError("rendered_inches must be positive")

    @property
    def value(self) -> float:
        return self.pixels / self.rendered_inches

    def scale_to(self, target_dpi: float) -> float:
        """Fraction to multiply pixel dimensions by to reach target_dpi (<=1.0)."""
        return min(1.0, target_dpi / self.value) if self.value else 1.0


# ── Cross-context raster vocabulary (moved from pdf_context 2026-07-15, W2) ──

PDF_POINTS_PER_INCH = 72.0
WHITE: tuple[int, int, int] = (255, 255, 255)
GUIDE_COLOR: tuple[int, int, int] = (187, 187, 187)  # #bbb — cut lines
DEFAULT_TARGET_KB = 1000


class ImageKind(str, Enum):
    BITONAL = "bitonal"  # 1-bit black/white — CCITT/Group4 territory
    GRAYSCALE = "grayscale"
    COLOR = "color"

    @property
    def is_contone(self) -> bool:
        return self is not ImageKind.BITONAL


class ResampleFilter(str, Enum):
    NEAREST = "nearest"  # bitonal only
    LANCZOS = "lanczos"  # contone


@dataclass(frozen=True)
class CompressionTarget:
    budget: ByteBudget
    quality_floor: QualityFloor = field(default_factory=QualityFloor)
    dpi_cap: int = 200  # contone cap: 150 screen / 225 print; 200 = balanced
    dpi_range: tuple[int, int] = (72, 300)
    quality_range: tuple[int, int] = (20, 95)  # JPEG encoder quality search bounds


class TargetSizeSearch:
    """Largest encoder quality whose output fits `slice_bytes`, respecting the floor.

    `encode` maps quality -> (num_bytes, PerceptualScore). Size must be monotonic
    non-decreasing in quality (true for JPEG/WebP). ~7 probes for a 20..95 range.
    One home for the quality binary search (DOMAIN.md §quality search).
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
            if size <= slice_bytes:
                if self._floor.accepts(score):
                    best = (q, score)
                lo = q  # try higher quality
            else:
                hi = q  # too big, lower quality
        return best


@dataclass(frozen=True)
class LosslessOutcome:
    """Result of a lossless pass (image or PDF). Hard rule #1 applies."""

    output: MediaFile
    before_bytes: int
    after_bytes: int
    changed: bool

    @property
    def saved_pct(self) -> float:
        return 100.0 * (1 - self.after_bytes / self.before_bytes) if self.before_bytes else 0.0
