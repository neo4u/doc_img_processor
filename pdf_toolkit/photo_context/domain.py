"""photo context — domain layer. Pure: no third-party imports.

Compliance specs are data presets (PRD §5): adding a country is adding a row to
PRESETS, never a code branch. See docs/LLD.md §2 and DOMAIN.md `photo` context.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class LayoutError(ValueError):
    """Sheet cannot fit at least one photo."""


@dataclass(frozen=True)
class PhotoSpec:
    """A passport-photo compliance preset. Data, not code."""

    name: str
    title: str
    width_px: int
    height_px: int
    dpi: int
    background: tuple[int, int, int] = (255, 255, 255)
    max_bytes: int | None = None  # portal upload ceiling (e.g. OCI 200 KB)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("photo dimensions must be positive")
        if self.dpi <= 0:
            raise ValueError("dpi must be positive")
        if self.max_bytes is not None and self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive when set")

    @property
    def aspect(self) -> float:
        return self.width_px / self.height_px

    @property
    def print_width_in(self) -> float:
        return self.width_px / self.dpi

    @property
    def print_height_in(self) -> float:
        return self.height_px / self.dpi

    def describe(self) -> dict[str, object]:
        """Serialization for /specs, list_photo_specs — one home (W2)."""
        return {
            "title": self.title,
            "pixels": f"{self.width_px}x{self.height_px}",
            "dpi": self.dpi,
            "max_bytes": self.max_bytes,
            "notes": self.notes,
        }


PRESETS: dict[str, PhotoSpec] = {
    "us_passport": PhotoSpec(
        name="us_passport",
        title="US Passport / Visa (2×2 in)",
        width_px=600,
        height_px=600,
        dpi=300,
        notes=(
            "Head must be 1–1.375 in (50–69% of image height), eyes 1.125–1.375 in "
            "from bottom. Neutral expression, both eyes open, plain white background, "
            "no glasses. Taken within last 6 months."
        ),
    ),
    "india_passport": PhotoSpec(
        name="india_passport",
        title="India Passport (2×2 in / 51×51 mm)",
        width_px=600,
        height_px=600,
        dpi=300,
        notes=(
            "Plain white background, full face frontal view, head 70–80% of frame. "
            "No glasses, neutral expression, dark clothing recommended against "
            "the white background."
        ),
    ),
    "india_oci": PhotoSpec(
        name="india_oci",
        title="India OCI (square JPEG, ≤ 200 KB)",
        width_px=600,
        height_px=600,
        dpi=300,
        max_bytes=200_000,
        notes=(
            "OCI portal: square JPEG ≤ 200 KB (most rejections are byte-size). "
            "Plain light background, full frontal face, no glasses, "
            "head centered with margin on all sides."
        ),
    ),
}


@dataclass(frozen=True)
class SheetSpec:
    """A print sheet size at a print DPI. 4x6 @ 300 → 1200×1800 px."""

    name: str
    width_in: float
    height_in: float
    dpi: int = 300

    def __post_init__(self) -> None:
        if self.width_in <= 0 or self.height_in <= 0 or self.dpi <= 0:
            raise ValueError("sheet dimensions and dpi must be positive")

    @property
    def width_px(self) -> int:
        return round(self.width_in * self.dpi)

    @property
    def height_px(self) -> int:
        return round(self.height_in * self.dpi)


SHEETS: dict[str, SheetSpec] = {
    "4x6": SheetSpec(name="4x6", width_in=4.0, height_in=6.0),
    "6x4": SheetSpec(name="6x4", width_in=6.0, height_in=4.0),
}


@dataclass(frozen=True)
class SheetLayout:
    """A computed tiling of identical photos onto a sheet (SheetLayoutService output)."""

    sheet: SheetSpec
    cols: int
    rows: int
    cell_w: int  # photo cell size on sheet, px
    cell_h: int
    x_offsets: list[int] = field(default_factory=list)  # left edge of each column
    y_offsets: list[int] = field(default_factory=list)  # top edge of each row

    @property
    def count(self) -> int:
        return self.cols * self.rows
