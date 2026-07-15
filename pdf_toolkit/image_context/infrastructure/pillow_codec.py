"""image context — Pillow adapter for ImageCodec."""

from __future__ import annotations

import io

from PIL import Image

from pdf_toolkit.image_context.ports import ImageCodec
from pdf_toolkit.shared_kernel import ResampleFilter

_PIL_FILTER = {
    ResampleFilter.NEAREST: Image.Resampling.NEAREST,
    ResampleFilter.LANCZOS: Image.Resampling.LANCZOS,
}


class PillowImageCodec(ImageCodec):
    def decode(self, data: bytes) -> Image.Image:
        return Image.open(io.BytesIO(data))

    def resize(self, img: Image.Image, width: int, height: int, resample: ResampleFilter) -> Image.Image:
        return img.resize((max(1, width), max(1, height)), _PIL_FILTER[resample])

    def encode(self, img: Image.Image, fmt: str, quality: int) -> bytes:
        buf = io.BytesIO()
        fmt = fmt.upper()
        if fmt in ("JPEG", "JPG"):
            rgb = img.convert("RGB") if img.mode not in ("RGB", "L") else img
            rgb.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        elif fmt == "PNG":
            img.save(buf, format="PNG", optimize=True)
        elif fmt == "TIFF":
            img.save(buf, format="TIFF", compression="group4")
        else:
            img.save(buf, format=fmt, quality=quality)
        return buf.getvalue()
