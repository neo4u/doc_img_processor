"""Shared test fixtures — setup/teardown lives here; test bodies assert business logic only.

Deterministic by construction: seeded RNG, no wall clock, no network.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def portrait(tmp_path: Path) -> Path:
    """A synthetic 'person against a wall': light bg + dark blob upper-center, 1200×1600 JPEG."""
    img = Image.new("RGB", (1200, 1600), (240, 240, 240))
    for y in range(400, 800):
        for x in range(400, 800):
            img.putpixel((x, y), (90, 70, 60))
    p = tmp_path / "portrait.jpg"
    img.save(p)
    return p


@pytest.fixture
def jpeg_bytes() -> bytes:
    """Noisy 1200×1600 JPEG bytes (unoptimized Huffman — room for lossless gains)."""
    rng = np.random.default_rng(1)
    img = Image.fromarray(rng.integers(80, 220, (1600, 1200, 3), dtype="uint8"), "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=False)
    return buf.getvalue()


@pytest.fixture
def scan_pdf(tmp_path: Path) -> Path:
    """A 3-page JPEG-in-PDF 'scan' via Pillow's PDF writer (structural slack included)."""
    rng = np.random.default_rng(3)
    pages = [Image.fromarray(rng.integers(100, 240, (800, 600, 3), dtype="uint8"), "RGB") for _ in range(3)]
    p = tmp_path / "scan.pdf"
    pages[0].save(p, save_all=True, append_images=pages[1:])
    return p


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient with lifespan events, torn down after the module."""
    from fastapi.testclient import TestClient

    from pdf_toolkit.api.app import app

    with TestClient(app) as c:
        yield c
