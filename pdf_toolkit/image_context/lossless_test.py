"""CompressImageLossless — pixels must be bit-exact; never larger (LLD §9)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from pdf_toolkit.image_context.application import CompressImageLossless
from pdf_toolkit.image_context.infrastructure.lossless import MozjpegPillowLosslessOptimizer
from pdf_toolkit.image_context.ports import UnsupportedFormat


@pytest.fixture
def compress() -> CompressImageLossless:
    return CompressImageLossless(MozjpegPillowLosslessOptimizer())


def _photo_like(tmp_path, ext, **save_kw):
    rng = np.random.default_rng(7)
    base = rng.integers(60, 200, (400, 400, 3), dtype="uint8")
    img = Image.fromarray(base, "RGB")
    p = tmp_path / f"src.{ext}"
    img.save(p, **save_kw)
    return p


def test_jpeg_pixels_bit_identical_and_smaller(compress, tmp_path):
    # Unoptimized-huffman JPEG (Pillow optimize=False) leaves room for mozjpeg.
    src = _photo_like(tmp_path, "jpg", quality=90, optimize=False)
    res = compress(src, tmp_path / "out.jpg")
    assert res.after_bytes < res.before_bytes and res.changed
    a = np.asarray(Image.open(src))
    b = np.asarray(Image.open(res.output.path))
    assert (a == b).all()  # lossless means lossless


def test_png_lossless(compress, tmp_path):
    src = _photo_like(tmp_path, "png", compress_level=1)
    res = compress(src, tmp_path / "out.png")
    assert res.after_bytes <= res.before_bytes
    a = np.asarray(Image.open(src))
    b = np.asarray(Image.open(res.output.path))
    assert (a == b).all()


def test_never_larger_hard_rule_1(compress, tmp_path):
    # Optimize twice: the second pass has nothing to gain and must copy unchanged.
    src = _photo_like(tmp_path, "jpg", quality=90, optimize=False)
    first = compress(src, tmp_path / "opt.jpg")
    second = compress(first.output.path, tmp_path / "opt2.jpg")
    assert second.after_bytes <= second.before_bytes
    if not second.changed:
        assert second.after_bytes == second.before_bytes


def test_unsupported_format_raises(compress, tmp_path):
    src = _photo_like(tmp_path, "webp")
    with pytest.raises(UnsupportedFormat):
        compress(src, tmp_path / "out.webp")


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
