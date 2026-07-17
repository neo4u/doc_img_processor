"""pdf context — zero-AGPL composite Compressor.

Stack: pikepdf (MPL-2.0, structural + surgical image-stream replacement)
     + Pillow (HPND, recompress loop via image_context)
     + pypdfium2 (BSD/Apache, used by the QualityMeter's renderer, not here).

Surgically rewrites each image XObject in place — never re-distills the whole file,
so fonts/annotations/vector content are untouched (unlike Ghostscript). This is the
license-clean primary path for the future hosted UI (no AGPL §13 network copyleft).
"""

from __future__ import annotations

import time
from pathlib import Path

import pikepdf
from pikepdf import Name

from pdf_toolkit.image_context.application import recompress_to_slice
from pdf_toolkit.image_context.infrastructure.pillow_codec import PillowImageCodec
from pdf_toolkit.image_context.infrastructure.ssim_meter import NumpySsimMeter
from pdf_toolkit.image_context.ports import ImageCodec, QualityMeter
from pdf_toolkit.pdf_context.domain import Codec, CompressionResult, DocumentCensus, EmbeddedImage
from pdf_toolkit.pdf_context.ports import Compressor
from pdf_toolkit.pdf_context.services import BudgetDecomposition
from pdf_toolkit.shared_kernel import (
    MAX_PDF_PAGES,
    CompressionTarget,
    EffectiveDpi,
    ImageKind,
    InvalidInput,
    MediaFile,
    Metric,
    PerceptualScore,
    UnreadableDocument,
    get_logger,
)

_log = get_logger(__name__)

_CS_KIND = {"/DeviceGray": ImageKind.GRAYSCALE, "/DeviceRGB": ImageKind.COLOR, "/DeviceCMYK": ImageKind.COLOR}


def _image_kind(obj) -> ImageKind:
    if int(obj.get("/BitsPerComponent", 8)) == 1:
        return ImageKind.BITONAL
    cs = obj.get("/ColorSpace")
    return _CS_KIND.get(str(cs), ImageKind.COLOR)


class PikepdfCompressor(Compressor):
    name = "pikepdf"

    def __init__(
        self,
        codec: ImageCodec | None = None,
        meter: QualityMeter | None = None,
        escalation: Compressor | None = None,
    ) -> None:
        self._codec = codec or PillowImageCodec()
        self._meter = meter or NumpySsimMeter()
        self._escalation = escalation

    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult:
        start = time.monotonic()
        ceiling = target.budget.ceiling()
        if source.size_bytes <= ceiling:
            # Validate even on the passthrough path — garbage in must not 200 out.
            try:
                pikepdf.open(source.path).close()
            except pikepdf.PdfError as e:
                raise UnreadableDocument(f"{source.path.name} is not a readable PDF: {e}") from e
            out.write_bytes(source.path.read_bytes())
            return self._result(source, out, 0, 0, None, start)

        try:
            pdf = pikepdf.open(source.path)
        except pikepdf.PasswordError as e:
            raise UnreadableDocument(f"{source.path.name} is password-protected") from e
        except pikepdf.PdfError as e:
            raise UnreadableDocument(f"{source.path.name} is not a readable PDF: {e}") from e
        try:
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise InvalidInput(f"{source.path.name} has {len(pdf.pages)} pages — cap is {MAX_PDF_PAGES}")
            # Pass 1: census — collect (object, EmbeddedImage) with geometry DPI.
            entries: list[tuple[pikepdf.Object, EmbeddedImage]] = []
            image_bytes = 0
            for pno, page in enumerate(pdf.pages):
                box = page.mediabox
                page_w_in = (float(box[2]) - float(box[0])) / 72.0
                page_h_in = (float(box[3]) - float(box[1])) / 72.0
                for _, obj in page.get_images().items():
                    w, h = int(obj.Width), int(obj.Height)
                    kind = _image_kind(obj)
                    try:
                        image_bytes += len(obj.read_raw_bytes())
                    except pikepdf.PdfError as e:
                        # Undercounting skews non_image_bytes and the budget split —
                        # make it visible instead of silently absorbing it.
                        _log.warning("census: unreadable image stream xref=%s: %s", obj.objgen[0], e)
                    eff = EffectiveDpi(pixels=w, rendered_inches=page_w_in or 1.0)
                    entries.append(
                        (
                            obj,
                            EmbeddedImage(
                                xref=obj.objgen[0],
                                page_index=pno,
                                width=w,
                                height=h,
                                kind=kind,
                                codec=Codec.JPEG,
                                effective_dpi=eff,
                                rendered_area_sqin=(page_w_in * page_h_in) or 1.0,
                            ),
                        )
                    )

            census = DocumentCensus(
                file=source,
                page_count=len(pdf.pages),
                images=[e for _, e in entries],
                non_image_bytes=max(0, source.size_bytes - image_bytes),
            )
            image_budget = max(1, ceiling - census.non_image_bytes)
            slices = BudgetDecomposition.allocate(census, image_budget)

            worst = PerceptualScore(Metric.SSIM, 1.0)
            dpi_used = q_used = 0
            for obj, img in entries:
                if img.kind is ImageKind.BITONAL:
                    continue  # CCITT G4 surgery: see DOMAIN.md; corpus has none
                original = obj.read_raw_bytes()
                outcome = recompress_to_slice(
                    original=original,
                    kind=img.kind,
                    width=img.width,
                    height=img.height,
                    effective_dpi=img.effective_dpi,
                    target=target,
                    slice_bytes=slices.get(img.xref, image_budget),
                    codec=self._codec,
                    meter=self._meter,
                )
                obj.write(outcome.data, filter=Name.DCTDecode)
                obj.Width, obj.Height = outcome.new_width, outcome.new_height
                obj.ColorSpace = Name.DeviceRGB
                obj.BitsPerComponent = 8
                worst = worst if worst.value <= outcome.score.value else outcome.score
                dpi_used, q_used = outcome.dpi_used, max(q_used, outcome.quality_used)

            pdf.save(out)  # qpdf structural pass (object streams) on save
        finally:
            pdf.close()

        after = out.stat().st_size
        if after >= source.size_bytes:  # hard rule #1
            out.write_bytes(source.path.read_bytes())
            return self._result(source, out, 0, 0, None, start)
        if after > ceiling and self._escalation is not None:  # BudgetMissed -> GS
            _log.warning(
                "budget missed (%d > %d bytes) — escalating %s -> %s",
                after,
                ceiling,
                self.name,
                self._escalation.name,
            )
            res = self._escalation.compress(source, target, out)
            return CompressionResult(
                output=res.output,
                engine=f"{self.name}->{res.engine}",
                before_bytes=res.before_bytes,
                after_bytes=res.after_bytes,
                dpi_used=res.dpi_used,
                quality_used=res.quality_used,
                score=res.score,
                elapsed_ms=int((time.monotonic() - start) * 1000),
                escalated=True,
            )
        return self._result(source, out, dpi_used, q_used, worst, start)

    def _result(self, source, out, dpi, q, score, start) -> CompressionResult:
        return CompressionResult(
            output=MediaFile.of(out),
            engine=self.name,
            before_bytes=source.size_bytes,
            after_bytes=Path(out).stat().st_size,
            dpi_used=dpi,
            quality_used=q,
            score=score,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            escalated=False,
        )
