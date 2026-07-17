"""photo context — Pillow adapter for PhotoRenderer (HEIC via pillow-heif)."""

from __future__ import annotations

import io
from pathlib import Path

import pillow_heif
from PIL import Image, ImageDraw, ImageOps

from pdf_toolkit.photo_context.ports import CropAnchor, GuideLine, PhotoRenderer, RgbColor
from pdf_toolkit.shared_kernel import GUIDE_COLOR, MAX_IMAGE_PIXELS, InvalidInput, UnreadableDocument

pillow_heif.register_heif_opener()  # makes Image.open understand .heic/.heif
# Reject-before-decode (W3): Pillow's default bomb threshold is too lax for a
# served path; DecompressionBombError fires past 2x this cap (imgproxy pattern).
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class PillowPhotoRenderer(PhotoRenderer[Image.Image]):
    def load(self, path: Path) -> Image.Image:
        try:
            img: Image.Image = Image.open(path)
            img = ImageOps.exif_transpose(img)  # phone photos carry orientation in EXIF
        except Image.DecompressionBombError as e:
            raise InvalidInput(f"image exceeds the {MAX_IMAGE_PIXELS:,}-pixel safety cap: {path.name}") from e
        except (OSError, SyntaxError) as e:  # PIL's unreadable-file surface
            raise UnreadableDocument(f"cannot read image {path.name}: {e}") from e
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode or "P" in img.mode else "RGB")
        return img

    def size(self, img: Image.Image) -> tuple[int, int]:
        return img.size

    def crop_to_aspect(self, img: Image.Image, aspect: float, anchor: CropAnchor) -> Image.Image:
        w, h = img.size
        if w / h > aspect:  # too wide — crop width
            crop_w, crop_h = round(h * aspect), h
        else:  # too tall — crop height
            crop_w, crop_h = w, round(w / aspect)
        # Center the crop on the anchor, clamped so the box stays in frame.
        cx, cy = anchor[0] * w, anchor[1] * h
        left = min(max(round(cx - crop_w / 2), 0), w - crop_w)
        top = min(max(round(cy - crop_h / 2), 0), h - crop_h)
        return img.crop((left, top, left + crop_w, top + crop_h))

    def resize(self, img: Image.Image, width: int, height: int) -> Image.Image:
        return img.resize((max(1, width), max(1, height)), Image.Resampling.LANCZOS)

    def flatten(self, img: Image.Image, background: RgbColor) -> Image.Image:
        if img.mode == "RGB":
            return img
        base = Image.new("RGB", img.size, background)
        rgba = img.convert("RGBA")
        base.paste(rgba, mask=rgba.getchannel("A"))
        return base

    def encode_jpeg(self, img: Image.Image, quality: int, dpi: int) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, dpi=(dpi, dpi), optimize=True, subsampling=1)
        return buf.getvalue()

    def compose(
        self,
        canvas_w: int,
        canvas_h: int,
        background: RgbColor,
        tiles: list[tuple[Image.Image, int, int]],
        guide_lines: list[GuideLine],
    ) -> Image.Image:
        canvas = Image.new("RGB", (canvas_w, canvas_h), background)
        for tile, x, y in tiles:
            canvas.paste(tile, (x, y))
        if guide_lines:
            draw = ImageDraw.Draw(canvas)
            for x0, y0, x1, y1 in guide_lines:
                draw.line((x0, y0, x1, y1), fill=GUIDE_COLOR, width=1)
        return canvas
