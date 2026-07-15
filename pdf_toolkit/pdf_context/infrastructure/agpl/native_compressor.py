"""pdf context — PyMuPDF (AGPL) composite Compressor.

Same target-size algorithm as PikepdfCompressor, sharing the per-image decision via
image_context.recompress_to_slice. Kept as an alternative engine: PyMuPDF is a single
fast dependency, but AGPL — prefer PikepdfCompressor for anything network-served.
"""
from __future__ import annotations

import time
from pathlib import Path

import fitz  # AGPL, confined here

from pdf_toolkit.image_context.application import recompress_to_slice
from pdf_toolkit.image_context.infrastructure.pillow_codec import PillowImageCodec
from pdf_toolkit.image_context.infrastructure.ssim_meter import NumpySsimMeter
from pdf_toolkit.image_context.ports import ImageCodec, QualityMeter
from pdf_toolkit.pdf_context.domain import (
    CompressionResult,
    CompressionTarget,
    ImageKind,
)
from pdf_toolkit.pdf_context.infrastructure.agpl.pymupdf_codec import PyMuPdfInspector
from pdf_toolkit.pdf_context.ports import Compressor, PdfInspector
from pdf_toolkit.pdf_context.services import BudgetDecomposition
from pdf_toolkit.shared_kernel import Metric, MediaFile, PerceptualScore


class NativeImageCompressor(Compressor):
    name = "pymupdf+pillow"

    def __init__(
        self,
        inspector: PdfInspector | None = None,
        codec: ImageCodec | None = None,
        meter: QualityMeter | None = None,
        escalation: Compressor | None = None,
    ) -> None:
        self._inspector = inspector or PyMuPdfInspector()
        self._codec = codec or PillowImageCodec()
        self._meter = meter or NumpySsimMeter()
        self._escalation = escalation

    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult:
        start = time.monotonic()
        ceiling = target.budget.ceiling()
        if source.size_bytes <= ceiling:
            out.write_bytes(source.path.read_bytes())
            return self._result(source, out, 0, 0, None, start)

        census = self._inspector.inspect(source)
        image_budget = max(1, ceiling - census.non_image_bytes)
        slices = BudgetDecomposition.allocate(census, image_budget)

        doc = fitz.open(source.path)
        worst = PerceptualScore(Metric.SSIM, 1.0)
        dpi_used = q_used = 0
        try:
            for img in census.images:
                if img.kind is ImageKind.BITONAL:
                    continue
                original = doc.extract_image(img.xref)["image"]
                outcome = recompress_to_slice(
                    original=original, kind=img.kind,
                    width=img.width, height=img.height,
                    effective_dpi=img.effective_dpi, target=target,
                    slice_bytes=slices.get(img.xref, image_budget),
                    codec=self._codec, meter=self._meter,
                )
                for page in doc:
                    if any(i[0] == img.xref for i in page.get_images(full=True)):
                        page.replace_image(img.xref, stream=outcome.data)
                        break
                worst = worst if worst.value <= outcome.score.value else outcome.score
                dpi_used, q_used = outcome.dpi_used, max(q_used, outcome.quality_used)
            doc.save(out, garbage=4, deflate=True, deflate_images=True)
        finally:
            doc.close()

        after = out.stat().st_size
        if after >= source.size_bytes:
            out.write_bytes(source.path.read_bytes())
            return self._result(source, out, 0, 0, None, start)
        if after > ceiling and self._escalation is not None:
            res = self._escalation.compress(source, target, out)
            return CompressionResult(
                output=res.output, engine=f"{self.name}->{res.engine}",
                before_bytes=res.before_bytes, after_bytes=res.after_bytes,
                dpi_used=res.dpi_used, quality_used=res.quality_used, score=res.score,
                elapsed_ms=int((time.monotonic() - start) * 1000), escalated=True,
            )
        return self._result(source, out, dpi_used, q_used, worst, start)

    def _result(self, source, out, dpi, q, score, start) -> CompressionResult:
        return CompressionResult(
            output=MediaFile.of(out), engine=self.name,
            before_bytes=source.size_bytes, after_bytes=Path(out).stat().st_size,
            dpi_used=dpi, quality_used=q, score=score,
            elapsed_ms=int((time.monotonic() - start) * 1000), escalated=False,
        )
