"""image context — SSIM quality meter (numpy box-window approximation).

Avoids a scipy/scikit-image dependency. Computes mean SSIM over an 8x8 uniform
window on the luma channel, images aligned to the smaller of the two sizes.
Good enough to *rank* engines; note it's a box-window (not Gaussian) SSIM.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from pdf_toolkit.image_context.ports import QualityMeter
from pdf_toolkit.shared_kernel import Metric, PerceptualScore

_C1 = (0.01 * 255) ** 2
_C2 = (0.03 * 255) ** 2
_WIN = 8


def _luma(data: bytes, size: tuple[int, int]) -> np.ndarray:
    img = Image.open(io.BytesIO(data)).convert("L").resize(size, Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float64)


def _box(a: np.ndarray, w: int) -> np.ndarray:
    """Mean over non-overlapping w x w blocks via cumulative sums (cheap)."""
    h, wd = a.shape
    h, wd = h - h % w, wd - wd % w
    a = a[:h, :wd].reshape(h // w, w, wd // w, w)
    return a.mean(axis=(1, 3))


class NumpySsimMeter(QualityMeter):
    def score(self, original: bytes, candidate: bytes) -> PerceptualScore:
        # Compare at a common, modest resolution — fast and resolution-independent.
        common = (1024, 768)
        x = _luma(original, common)
        y = _luma(candidate, common)

        mx, my = _box(x, _WIN), _box(y, _WIN)
        mxx = _box(x * x, _WIN) - mx * mx
        myy = _box(y * y, _WIN) - my * my
        mxy = _box(x * y, _WIN) - mx * my

        ssim_map = ((2 * mx * my + _C1) * (2 * mxy + _C2)) / ((mx * mx + my * my + _C1) * (mxx + myy + _C2))
        return PerceptualScore(Metric.SSIM, float(np.clip(ssim_map.mean(), 0.0, 1.0)))
