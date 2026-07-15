"""CompressPdfLossless — page rasters byte-identical pre/post (LLD §9)."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from pdf_toolkit.pdf_context.application import CompressPdfLossless
from pdf_toolkit.pdf_context.infrastructure.pikepdf_lossless import PikepdfStructuralOptimizer


@pytest.fixture
def compress() -> CompressPdfLossless:
    return CompressPdfLossless(PikepdfStructuralOptimizer())


def _scan_like_pdf(tmp_path):
    """A JPEG-in-PDF 'scan' via Pillow's PDF writer (uncompressed xref, no objstm
    — exactly the structural slack the optimizer should reclaim)."""
    rng = np.random.default_rng(3)
    pages = [Image.fromarray(rng.integers(100, 240, (800, 600, 3), dtype="uint8"), "RGB") for _ in range(3)]
    p = tmp_path / "scan.pdf"
    pages[0].save(p, save_all=True, append_images=pages[1:])
    return p


def _render_page1(pdf_path) -> bytes:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        buf = io.BytesIO()
        doc[0].render(scale=1.0).to_pil().save(buf, format="PNG")
        return buf.getvalue()
    finally:
        doc.close()


def test_raster_bit_identical_and_not_larger(compress, tmp_path):
    src = _scan_like_pdf(tmp_path)
    res = compress(src, tmp_path / "out.pdf")
    assert res.after_bytes <= res.before_bytes  # hard rule #1
    assert _render_page1(src) == _render_page1(res.output.path)


def test_strip_metadata_keeps_rasters(compress, tmp_path):
    src = _scan_like_pdf(tmp_path)
    res = compress(src, tmp_path / "out.pdf", strip_metadata=True)
    assert _render_page1(src) == _render_page1(res.output.path)


def test_missing_input_raises(compress, tmp_path):
    with pytest.raises(FileNotFoundError):
        compress(tmp_path / "nope.pdf", tmp_path / "out.pdf")


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
