"""CreatePassportPhoto / ComposePrintSheet — spec conformance (LLD §9)."""

from __future__ import annotations

from pathlib import Path

import pillow_heif
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


@pytest.fixture
def create() -> CreatePassportPhoto:
    return CreatePassportPhoto(PillowPhotoRenderer(), CenterFaceLocator())


def _portrait(tmp_path: Path, w: int = 1200, h: int = 1600, ext: str = "jpg") -> Path:
    """A synthetic 'person against a wall': gradient bg + dark blob upper-center."""
    img = Image.new("RGB", (w, h), (240, 240, 240))
    for y in range(h // 4, h // 2):
        for x in range(w // 3, 2 * w // 3):
            img.putpixel((x, y), (90, 70, 60))
    p = tmp_path / f"src.{ext}"
    img.save(p)
    return p


def test_output_matches_spec_exactly(create, tmp_path):
    out = tmp_path / "out.jpg"
    res = create(_portrait(tmp_path), PRESETS["us_passport"], out)
    img = Image.open(out)
    assert img.size == (600, 600)
    assert img.info["dpi"] == (300, 300)  # photo hard rule #3
    assert img.format == "JPEG"
    assert not res.upscaled and res.warnings == []


@pytest.mark.slow  # 2000×2000 noisy encode ×~7 probes
def test_oci_respects_200kb_ceiling(create, tmp_path):
    import numpy as np

    # noisy image → hard to compress → forces the quality search to work
    rng = np.random.default_rng(42)
    noisy = Image.fromarray(rng.integers(0, 255, (2000, 2000, 3), dtype="uint8"), "RGB")
    src = tmp_path / "noisy.jpg"
    noisy.save(src, quality=98)
    res = create(src, PRESETS["india_oci"], tmp_path / "oci.jpg")
    assert res.output.size_bytes <= 200_000
    assert res.quality_used < 95  # ceiling actually engaged


def test_heic_input_round_trips(create, tmp_path):
    src_img = Image.open(_portrait(tmp_path))
    heic = tmp_path / "src.heic"
    pillow_heif.from_pillow(src_img).save(heic)
    res = create(heic, PRESETS["india_passport"], tmp_path / "out.jpg")
    assert Image.open(res.output.path).size == (600, 600)


def test_exif_orientation_is_applied(create, tmp_path):
    # Landscape pixels + EXIF orientation 6 (rotate 90 CW) = logical portrait.
    img = Image.new("RGB", (1600, 1200), (200, 200, 200))
    exif = Image.Exif()
    exif[274] = 6  # 274 = Orientation
    src = tmp_path / "rot.jpg"
    img.save(src, exif=exif)
    res = create(src, PRESETS["us_passport"], tmp_path / "out.jpg")
    assert res.source_px == (1200, 1600)  # transposed before any cropping


def test_low_res_source_warns_and_flags_upscaled(create, tmp_path):
    res = create(_portrait(tmp_path, 300, 400), PRESETS["us_passport"], tmp_path / "out.jpg")
    assert res.upscaled  # photo hard rule #2
    assert any("upscaled" in w for w in res.warnings)


def test_missing_input_raises(create, tmp_path):
    with pytest.raises(FileNotFoundError):
        create(tmp_path / "nope.jpg", PRESETS["us_passport"], tmp_path / "out.jpg")


def test_sheet_is_6_up_4x6_at_300dpi(create, tmp_path):
    photo = tmp_path / "photo.jpg"
    create(_portrait(tmp_path), PRESETS["us_passport"], photo)
    res = ComposePrintSheet(PillowPhotoRenderer())(photo, SHEETS["4x6"], tmp_path / "sheet.jpg")
    img = Image.open(res.output.path)
    assert img.size == (1200, 1800)
    assert img.info["dpi"] == (300, 300)
    assert res.count == 6


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
