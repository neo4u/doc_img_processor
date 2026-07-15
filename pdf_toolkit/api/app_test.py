"""HTTP API round-trips via TestClient (LLD §9)."""

from __future__ import annotations

import io

import httpx2  # noqa: F401 — starlette.testclient needs it at runtime; import makes gazelle wire the dep
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from pdf_toolkit.api.app import app

client = TestClient(app)


def _jpeg_bytes(w=1200, h=1600) -> bytes:
    rng = np.random.default_rng(1)
    img = Image.fromarray(rng.integers(80, 220, (h, w, 3), dtype="uint8"), "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=False)
    return buf.getvalue()


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_specs_lists_presets():
    specs = client.get("/specs").json()
    assert {"us_passport", "india_passport", "india_oci"} <= set(specs)


def test_photo_round_trip():
    r = client.post("/photo?spec=india_oci", files={"file": ("me.jpg", _jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 200
    img = Image.open(io.BytesIO(r.content))
    assert img.size == (600, 600)
    assert len(r.content) <= 200_000


def test_photo_unknown_spec_is_422():
    r = client.post("/photo?spec=mars_visa", files={"file": ("me.jpg", _jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 422


def test_sheet_round_trip():
    photo = client.post(
        "/photo?spec=us_passport", files={"file": ("me.jpg", _jpeg_bytes(), "image/jpeg")}
    ).content
    r = client.post("/sheet?size=4x6", files={"file": ("photo.jpg", photo, "image/jpeg")})
    assert r.status_code == 200
    assert Image.open(io.BytesIO(r.content)).size == (1200, 1800)
    assert r.headers["x-photos"] == "6"


def test_lossless_round_trip():
    r = client.post("/compress/lossless", files={"file": ("scan.jpg", _jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 200
    assert int(r.headers["x-after-bytes"]) <= int(r.headers["x-before-bytes"])


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
