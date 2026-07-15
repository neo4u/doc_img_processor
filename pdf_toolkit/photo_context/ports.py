"""photo context — ports.

PhotoRenderer is generic over the adapter's opaque image handle (ImageT):
the Pillow adapter binds ImageT=PIL.Image.Image, the application layer stays
adapter-agnostic, and nothing is typed `Any` (DOMAIN.md hard rule #6).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

ImageT = TypeVar("ImageT")

GuideLine = tuple[int, int, int, int]  # x0, y0, x1, y1
RgbColor = tuple[int, int, int]
CropAnchor = tuple[float, float]  # fractions of image size, 0..1


class FaceLocator(ABC):
    """Where should the crop be centered? Returns fractions of image size (0..1)."""

    @abstractmethod
    def anchor(self, img_w: int, img_h: int) -> CropAnchor: ...


class CenterFaceLocator(FaceLocator):
    """v1 null-adapter: geometric center, biased slightly up — faces sit above
    the geometric center in typical phone portraits. A CV adapter can replace
    this without touching the application layer (LLD §3)."""

    def anchor(self, img_w: int, img_h: int) -> CropAnchor:
        return (0.5, 0.45)


class PhotoRenderer(ABC, Generic[ImageT]):
    """Raster operations for photo production."""

    @abstractmethod
    def load(self, path: Path) -> ImageT:
        """Decode HEIC/JPG/PNG, apply EXIF orientation, return RGB(A) image."""

    @abstractmethod
    def size(self, img: ImageT) -> tuple[int, int]: ...

    @abstractmethod
    def crop_to_aspect(self, img: ImageT, aspect: float, anchor: CropAnchor) -> ImageT:
        """Largest crop of the given aspect ratio, centered as close to anchor
        as the frame allows."""

    @abstractmethod
    def resize(self, img: ImageT, width: int, height: int) -> ImageT: ...

    @abstractmethod
    def flatten(self, img: ImageT, background: RgbColor) -> ImageT:
        """Composite any alpha onto a solid background; return RGB."""

    @abstractmethod
    def encode_jpeg(self, img: ImageT, quality: int, dpi: int) -> bytes: ...

    @abstractmethod
    def compose(
        self,
        canvas_w: int,
        canvas_h: int,
        background: RgbColor,
        tiles: list[tuple[ImageT, int, int]],
        guide_lines: list[GuideLine],
    ) -> ImageT:
        """Paste tiles at (x, y); draw 1-px guide lines."""
