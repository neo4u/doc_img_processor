"""NumpySsimMeter sanity: the floor's measuring stick must itself measure (W4)."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from pdf_toolkit.image_context.infrastructure.ssim_meter import NumpySsimMeter


def _png(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def meter() -> NumpySsimMeter:
    return NumpySsimMeter()


def test_identical_images_score_1(meter):
    rng = np.random.default_rng(2)
    img = _png(rng.integers(0, 255, (256, 256, 3), dtype="uint8"))
    assert meter.score(img, img).value == pytest.approx(1.0, abs=1e-6)


def test_heavy_degradation_scores_lower_than_light(meter):
    rng = np.random.default_rng(2)
    base = rng.integers(60, 200, (256, 256, 3), dtype="uint8")
    light = base + rng.integers(-5, 5, base.shape).astype("int16")
    heavy = rng.integers(0, 255, base.shape, dtype="uint8")  # unrelated noise
    s_light = meter.score(_png(base), _png(np.clip(light, 0, 255).astype("uint8"))).value
    s_heavy = meter.score(_png(base), _png(heavy)).value
    assert s_heavy < s_light < 1.0  # ordering is the property that matters


def test_scores_are_ssim_metric(meter):
    from pdf_toolkit.shared_kernel import Metric

    rng = np.random.default_rng(2)
    img = _png(rng.integers(0, 255, (64, 64, 3), dtype="uint8"))
    assert meter.score(img, img).metric is Metric.SSIM


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
