"""MCP tools: W3 confinement/no-clobber contracts + direct-call round-trips (W4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

import pdf_toolkit.mcp_server.server as srv
from pdf_toolkit.shared_kernel import InvalidInput


@pytest.fixture
def confined(monkeypatch, tmp_path: Path) -> Path:
    """Fence the server into tmp_path for the duration of a test."""
    monkeypatch.setattr(srv, "ALLOWED_DIRS", [tmp_path.resolve()])
    return tmp_path


def _photo(path: Path, w=800, h=800) -> Path:
    Image.new("RGB", (w, h), (220, 220, 220)).save(path)
    return path


def test_input_outside_allowlist_rejected(confined):
    with pytest.raises(InvalidInput, match="allowed directories"):
        srv._resolve("/etc/hosts")


def test_output_outside_allowlist_rejected(confined, tmp_path):
    src = _photo(tmp_path / "p.jpg")
    with pytest.raises(InvalidInput, match="allowed directories"):
        srv.create_passport_photo(str(src), out_path="/tmp/elsewhere.jpg")


def test_no_clobber_unless_overwrite(confined, tmp_path):
    src = _photo(tmp_path / "p.jpg")
    out = tmp_path / "out.jpg"
    out.write_bytes(b"precious existing file")
    with pytest.raises(InvalidInput, match="already exists"):
        srv.create_passport_photo(str(src), out_path=str(out), sheet="none")
    res = srv.create_passport_photo(str(src), out_path=str(out), sheet="none", overwrite=True)
    assert Path(res["photo"]) == out
    assert out.stat().st_size > 100  # actually replaced


def test_photo_round_trip_and_sheet(confined, tmp_path):
    src = _photo(tmp_path / "p.jpg")
    res = srv.create_passport_photo(str(src), spec="india_oci")
    assert res["bytes"] <= 200_000
    assert Path(res["photo"]).exists() and Path(res["sheet"]).exists()
    assert res["sheet_photos"] == 6


def test_unknown_spec_lists_valid_options(confined, tmp_path):
    src = _photo(tmp_path / "p.jpg")
    with pytest.raises(ValueError, match="india_oci"):
        srv.create_passport_photo(str(src), spec="mars_visa")


def test_merge_and_inspect(confined, tmp_path):
    import numpy as np

    rng = np.random.default_rng(5)
    pages = [Image.fromarray(rng.integers(100, 240, (400, 300, 3), dtype="uint8"), "RGB") for _ in range(2)]
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    pages[0].save(a)
    pages[1].save(b)
    merged = srv.merge_pdfs([str(a), str(b)], str(tmp_path / "m.pdf"))
    assert merged["pages"] == 2
    census = srv.inspect_pdf(str(tmp_path / "m.pdf"))
    assert census["pages"] == 2 and len(census["images"]) == 2


def test_negative_target_kb_rejected(confined, tmp_path):
    src = tmp_path / "x.pdf"
    Image.new("RGB", (100, 100)).save(src)
    with pytest.raises(InvalidInput, match="positive"):
        srv.compress_pdf(str(src), target_kb=-5)


def test_list_allowed_dirs_reports_fence(confined, tmp_path):
    assert srv.list_allowed_dirs() == {"allowed_dirs": [str(tmp_path.resolve())]}


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
