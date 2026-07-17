"""W3 serving-hardening contracts: caps, typed errors, correlation ids (LLD §Errors)."""

from __future__ import annotations

import io

import httpx2  # noqa: F401 — starlette TestClient runtime dep; makes gazelle wire it
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import pdf_toolkit.api.app as app_module

client = TestClient(app_module.app, raise_server_exceptions=False)


def _jpeg(w=200, h=200) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 200, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def test_oversize_upload_is_413(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_BYTES", 1000)
    r = client.post("/photo", files={"file": ("big.jpg", _jpeg(800, 800), "image/jpeg")})
    assert r.status_code == 413
    assert "cap" in r.json()["detail"]


def test_corrupt_pdf_is_422_not_500():
    r = client.post("/inspect", files={"file": ("fake.pdf", b"not a pdf at all", "application/pdf")})
    assert r.status_code == 422
    assert "not a readable PDF" in r.json()["detail"]


def test_corrupt_pdf_compress_is_422():
    r = client.post("/compress/target?kb=100", files={"file": ("fake.pdf", b"junk", "application/pdf")})
    assert r.status_code == 422


def test_decompression_bomb_is_422(monkeypatch):
    # Shrink Pillow's cap so a normal image trips DecompressionBombError,
    # which the renderer maps to InvalidInput -> 422.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)
    r = client.post("/photo", files={"file": ("bomb.jpg", _jpeg(400, 400), "image/jpeg")})
    assert r.status_code == 422
    assert "pixel" in r.json()["detail"]


def test_correlation_id_echoed_and_minted():
    r = client.get("/healthz", headers={"X-Correlation-Id": "test-cid-42"})
    assert r.headers["x-correlation-id"] == "test-cid-42"
    r2 = client.get("/healthz")
    assert len(r2.headers["x-correlation-id"]) >= 8  # minted


def test_unhandled_errors_return_500_with_cid(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(app_module, "_save_upload", boom)
    r = client.post("/photo", files={"file": ("x.jpg", _jpeg(), "image/jpeg")})
    assert r.status_code == 500
    assert "cid=" in r.json()["detail"]  # diagnosable, not blank


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
