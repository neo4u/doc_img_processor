"""photo context — application use cases.

CreatePassportPhoto: JPG/HEIC → spec-conformant JPEG (exact px, DPI, white bg,
optional byte ceiling via the shared quality binary search — DOMAIN.md §quality search).
ComposePrintSheet: passport photo → N-up 4×6/6×4 print sheet with cut guides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic

from pdf_toolkit.photo_context.domain import PhotoSpec, SheetLayout, SheetSpec
from pdf_toolkit.photo_context.ports import FaceLocator, GuideLine, ImageT, PhotoRenderer
from pdf_toolkit.photo_context.services import SheetLayoutService
from pdf_toolkit.shared_kernel import (
    GUIDE_COLOR,  # noqa: F401 — re-exported for renderers
    WHITE,
    MediaFile,
    Metric,
    PerceptualScore,
    QualityFloor,
    TargetSizeSearch,
)

_Q_MAX = 95  # visually transparent JPEG; also the no-ceiling default
_Q_MIN = 60  # below this a compliance photo is not acceptable


@dataclass(frozen=True)
class PhotoResult:
    output: MediaFile
    spec: PhotoSpec
    quality_used: int
    source_px: tuple[int, int]
    upscaled: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class CreatePassportPhoto(Generic[ImageT]):
    renderer: PhotoRenderer[ImageT]
    locator: FaceLocator

    def __call__(self, input_path: str | Path, spec: PhotoSpec, out_path: str | Path) -> PhotoResult:
        source = MediaFile.of(input_path)
        if not source.exists:
            raise FileNotFoundError(f"file not found: {source.path}")

        img = self.renderer.load(source.path)
        src_w, src_h = self.renderer.size(img)

        warnings: list[str] = []
        upscaled = src_w < spec.width_px or src_h < spec.height_px
        if upscaled:  # photo hard rule #2: never upscale silently
            warnings.append(
                f"source is {src_w}×{src_h} px, below the {spec.width_px}×{spec.height_px} "
                f"spec — output is upscaled and may look soft when printed"
            )

        anchor = self.locator.anchor(src_w, src_h)
        img = self.renderer.crop_to_aspect(img, spec.aspect, anchor)
        img = self.renderer.resize(img, spec.width_px, spec.height_px)
        img = self.renderer.flatten(img, spec.background)

        quality, data = self._encode_under_ceiling(img, spec)
        if spec.max_bytes is not None and len(data) > spec.max_bytes:
            warnings.append(
                f"could not reach {spec.max_bytes} bytes even at quality {_Q_MIN}; "
                f"output is {len(data)} bytes"
            )

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return PhotoResult(
            output=MediaFile.of(out),
            spec=spec,
            quality_used=quality,
            source_px=(src_w, src_h),
            upscaled=upscaled,
            warnings=warnings,
        )

    def _encode_under_ceiling(self, img: ImageT, spec: PhotoSpec) -> tuple[int, bytes]:
        """Largest quality whose encoding fits max_bytes.

        Reuses the shared TargetSizeSearch (one algorithm home, DOMAIN.md §quality
        search) with a permissive floor — photos have no perceptual meter; the
        quality floor here is the _Q_MIN bound itself. Encodes are memoized so the
        winner is never re-encoded.
        """
        if spec.max_bytes is None:
            return _Q_MAX, self.renderer.encode_jpeg(img, _Q_MAX, spec.dpi)

        cache: dict[int, bytes] = {_Q_MAX: self.renderer.encode_jpeg(img, _Q_MAX, spec.dpi)}
        if len(cache[_Q_MAX]) <= spec.max_bytes:
            return _Q_MAX, cache[_Q_MAX]

        def encode(q: int) -> tuple[int, PerceptualScore]:
            cache[q] = self.renderer.encode_jpeg(img, q, spec.dpi)
            return len(cache[q]), PerceptualScore(Metric.SSIM, 1.0)

        search = TargetSizeSearch((_Q_MIN, _Q_MAX), QualityFloor(Metric.SSIM, 0.0))
        chosen = search.best_quality(spec.max_bytes, encode)
        if chosen is None:  # even _Q_MIN over ceiling — return it, caller warns
            return _Q_MIN, self.renderer.encode_jpeg(img, _Q_MIN, spec.dpi)
        return chosen[0], cache[chosen[0]]


@dataclass(frozen=True)
class SheetResult:
    output: MediaFile
    layout: SheetLayout
    count: int


@dataclass
class ComposePrintSheet(Generic[ImageT]):
    renderer: PhotoRenderer[ImageT]

    def __call__(
        self,
        photo_path: str | Path,
        sheet: SheetSpec,
        out_path: str | Path,
        photo_size_in: float = 2.0,
        guides: bool = True,
    ) -> SheetResult:
        source = MediaFile.of(photo_path)
        if not source.exists:
            raise FileNotFoundError(f"file not found: {source.path}")

        layout = SheetLayoutService.layout(photo_size_in, photo_size_in, sheet)

        img = self.renderer.load(source.path)
        img = self.renderer.flatten(img, WHITE)
        tile = self.renderer.resize(img, layout.cell_w, layout.cell_h)

        tiles = [(tile, x, y) for y in layout.y_offsets for x in layout.x_offsets]
        guide_lines = self._guides(layout) if guides else []

        canvas = self.renderer.compose(
            sheet.width_px,
            sheet.height_px,
            WHITE,
            tiles,
            guide_lines,
        )
        data = self.renderer.encode_jpeg(canvas, _Q_MAX, sheet.dpi)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return SheetResult(output=MediaFile.of(out), layout=layout, count=layout.count)

    @staticmethod
    def _guides(layout: SheetLayout) -> list[GuideLine]:
        """Full-bleed cut lines along every cell boundary (both edges of each cell)."""
        w, h = layout.sheet.width_px, layout.sheet.height_px
        xs = {x for cx in layout.x_offsets for x in (cx, cx + layout.cell_w)}
        ys = {y for cy in layout.y_offsets for y in (cy, cy + layout.cell_h)}
        lines = [(min(max(x, 0), w - 1), 0, min(max(x, 0), w - 1), h - 1) for x in sorted(xs)]
        lines += [(0, min(max(y, 0), h - 1), w - 1, min(max(y, 0), h - 1)) for y in sorted(ys)]
        return lines
