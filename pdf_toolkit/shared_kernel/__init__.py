"""Shared kernel — value objects used across the pdf and image contexts.

Immutable, validated on construction, no third-party imports. These names are the
ubiquitous language; Rust and Go mirror them exactly. See ../../DOMAIN.md.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Metric(str, Enum):
    SSIM = "ssim"          # higher is better, 0..1
    DSSIM = "dssim"        # lower is better, 0..
    BUTTERAUGLI = "butteraugli"

    @property
    def higher_is_better(self) -> bool:
        return self is Metric.SSIM


@dataclass(frozen=True)
class MediaFile:
    """A file on disk. Identity is its content hash."""
    path: Path

    @classmethod
    def of(cls, path: str | Path) -> "MediaFile":
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

    @property
    def content_hash(self) -> str:
        h = hashlib.sha256()
        h.update(self.path.read_bytes())
        return h.hexdigest()


@dataclass(frozen=True)
class ByteBudget:
    """A target size with tolerance. Default: never over target, no lower bound."""
    target_bytes: int
    over_tolerance: float = 0.0   # fraction the ceiling may exceed target (e.g. 0.05)

    def __post_init__(self) -> None:
        if self.target_bytes <= 0:
            raise ValueError("target_bytes must be positive")
        if self.over_tolerance < 0:
            raise ValueError("over_tolerance must be >= 0")

    @classmethod
    def kb(cls, kb: int, over_tolerance: float = 0.0) -> "ByteBudget":
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

    def is_at_least(self, other: "PerceptualScore | float") -> bool:
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
