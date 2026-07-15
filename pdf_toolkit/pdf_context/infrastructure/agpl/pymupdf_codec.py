"""pdf context — PyMuPDF adapter: inspector + image-surgery codec.

Isolates the AGPL MuPDF dependency (fitz) behind the PdfInspector/PdfCodec ports.
Effective DPI is computed from page geometry (rendered rect), never image metadata
(hard rule #3).
"""

from __future__ import annotations

import fitz  # PyMuPDF (AGPL) — confined to this module

from pdf_toolkit.pdf_context.domain import Codec, DocumentCensus, EmbeddedImage
from pdf_toolkit.pdf_context.ports import PdfInspector
from pdf_toolkit.shared_kernel import EffectiveDpi, ImageKind, MediaFile

_CS_KIND = {1: ImageKind.GRAYSCALE, 3: ImageKind.COLOR, 4: ImageKind.COLOR}
_EXT_CODEC = {
    "jpeg": Codec.JPEG,
    "jpg": Codec.JPEG,
    "png": Codec.PNG,
    "jbig2": Codec.JBIG2,
    "fax": Codec.CCITT_G4,
}


def _kind(cs: int, bpc: int) -> ImageKind:
    if bpc == 1:
        return ImageKind.BITONAL
    return _CS_KIND.get(cs, ImageKind.COLOR)


class PyMuPdfInspector(PdfInspector):
    def inspect(self, source: MediaFile) -> DocumentCensus:
        doc = fitz.open(source.path)
        images: list[EmbeddedImage] = []
        image_bytes = 0
        try:
            for pno, page in enumerate(doc):
                rect = page.rect
                page_w_in = rect.width / 72.0
                page_h_in = rect.height / 72.0
                for info in page.get_images(full=True):
                    xref = info[0]
                    d = doc.extract_image(xref)
                    w, h, ext = d["width"], d["height"], d.get("ext", "")
                    bpc = d.get("bpc", 8)
                    cs = d.get("colorspace", 3)
                    image_bytes += len(d.get("image", b""))
                    # Effective DPI from the horizontal geometry of the page.
                    eff = EffectiveDpi(pixels=w, rendered_inches=page_w_in or 1.0)
                    images.append(
                        EmbeddedImage(
                            xref=xref,
                            page_index=pno,
                            width=w,
                            height=h,
                            kind=_kind(cs, bpc),
                            codec=_EXT_CODEC.get(ext, Codec.RAW),
                            effective_dpi=eff,
                            rendered_area_sqin=(page_w_in * page_h_in) or 1.0,
                        )
                    )
            non_image = max(0, source.size_bytes - image_bytes)
            return DocumentCensus(
                file=source,
                page_count=doc.page_count,
                images=images,
                non_image_bytes=non_image,
            )
        finally:
            doc.close()
