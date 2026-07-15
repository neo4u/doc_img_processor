"""image context — lossless optimizer adapter.

JPEG: mozjpeg entropy-coding-only optimization (Huffman tables + progressive scan
scripts) — the DCT coefficients are untouched, so decoded pixels are bit-identical.
PNG: Pillow re-save at max zlib effort — lossless by format.
"""

from __future__ import annotations

import io

import mozjpeg_lossless_optimization
from PIL import Image

from pdf_toolkit.image_context.ports import LosslessOptimizer, UnsupportedFormat


class MozjpegPillowLosslessOptimizer(LosslessOptimizer):
    def optimize(self, data: bytes, fmt: str) -> bytes:
        fmt = fmt.lower().lstrip(".")
        if fmt in ("jpg", "jpeg"):
            return mozjpeg_lossless_optimization.optimize(data)
        if fmt == "png":
            img = Image.open(io.BytesIO(data))
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True, compress_level=9)
            return buf.getvalue()
        raise UnsupportedFormat(f"lossless optimization not supported for .{fmt} (supported: jpg, jpeg, png)")
