"""Performance budgets (`-m perf`) and stress (`-m manual`) — excluded from default runs.

Budgets are generous fences against regression, not benchmarks: a 3× slowdown
should fail; normal variance should not.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PIL import Image

from pdf_toolkit.photo_context import (
    PRESETS,
    SHEETS,
    CenterFaceLocator,
    ComposePrintSheet,
    CreatePassportPhoto,
)
from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer


@pytest.mark.perf
def test_photo_under_one_second(portrait, tmp_path):
    renderer = PillowPhotoRenderer()
    t0 = time.monotonic()
    CreatePassportPhoto(renderer, CenterFaceLocator())(portrait, PRESETS["us_passport"], tmp_path / "p.jpg")
    assert time.monotonic() - t0 < 1.0


@pytest.mark.perf
def test_sheet_under_one_second(portrait, tmp_path):
    renderer = PillowPhotoRenderer()
    photo = tmp_path / "p.jpg"
    CreatePassportPhoto(renderer, CenterFaceLocator())(portrait, PRESETS["us_passport"], photo)
    t0 = time.monotonic()
    ComposePrintSheet(renderer)(photo, SHEETS["4x6"], tmp_path / "s.jpg")
    assert time.monotonic() - t0 < 1.0


@pytest.mark.perf
def test_compress_3page_scan_under_10s(scan_pdf, tmp_path):
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
    from pdf_toolkit.shared_kernel import ByteBudget, CompressionTarget, MediaFile, Metric, QualityFloor

    target = CompressionTarget(
        budget=ByteBudget.kb(max(20, scan_pdf.stat().st_size // 2000)),
        quality_floor=QualityFloor(Metric.SSIM, 0.0),
    )
    t0 = time.monotonic()
    PikepdfCompressor().compress(MediaFile.of(scan_pdf), target, tmp_path / "o.pdf")
    assert time.monotonic() - t0 < 10.0


@pytest.mark.manual
def test_stress_50_page_scan(tmp_path):
    """Near the MAX_PDF_PAGES envelope; must finish, not corrupt, not OOM."""
    from pdf_toolkit.pdf_context.application import InspectDocument
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_inspector import PikepdfInspector

    rng = np.random.default_rng(11)
    pages = [Image.fromarray(rng.integers(80, 230, (1100, 850, 3), dtype="uint8"), "RGB") for _ in range(50)]
    big = tmp_path / "big.pdf"
    pages[0].save(big, save_all=True, append_images=pages[1:])
    census = InspectDocument(PikepdfInspector())(big)
    assert census.page_count == 50 and len(census.images) == 50


@pytest.mark.manual
def test_stress_concurrent_api_photos(portrait):
    """Threadpool sanity: 8 concurrent /photo round-trips, all 200."""
    from concurrent.futures import ThreadPoolExecutor

    from fastapi.testclient import TestClient

    from pdf_toolkit.api.app import app

    data = portrait.read_bytes()
    with TestClient(app) as client:

        def one(_: int) -> int:
            r = client.post("/photo?spec=us_passport", files={"file": ("p.jpg", data, "image/jpeg")})
            return r.status_code

        with ThreadPoolExecutor(max_workers=8) as pool:
            assert all(code == 200 for code in pool.map(one, range(8)))


if __name__ == "__main__":
    import sys

    # Bazel/py_test entrypoint: perf budgets only. `manual` stress runs are
    # invoked explicitly: .venv/bin/pytest -m manual
    sys.exit(pytest.main([__file__, "-q", "-m", "perf"]))
