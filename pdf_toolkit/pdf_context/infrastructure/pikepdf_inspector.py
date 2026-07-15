"""pdf context — license-clean PdfInspector (pikepdf, MPL-2.0).

The served surfaces (MCP, HTTP) must never import AGPL code (PRD N2); this
inspector replaces PyMuPdfInspector on those paths. Codec is read from the
stream's /Filter (never assumed), kind from BitsPerComponent + ColorSpace.
DPI remains the mediabox approximation until the W5 CTM census lands.
"""

from __future__ import annotations

import contextlib

import pikepdf

from pdf_toolkit.pdf_context.domain import Codec, DocumentCensus, EmbeddedImage
from pdf_toolkit.pdf_context.ports import PdfInspector
from pdf_toolkit.shared_kernel import EffectiveDpi, ImageKind, MediaFile

_CS_KIND = {
    "/DeviceGray": ImageKind.GRAYSCALE,
    "/DeviceRGB": ImageKind.COLOR,
    "/DeviceCMYK": ImageKind.COLOR,
}
_FILTER_CODEC = {
    "/DCTDecode": Codec.JPEG,
    "/CCITTFaxDecode": Codec.CCITT_G4,
    "/FlateDecode": Codec.FLATE,
    "/JBIG2Decode": Codec.JBIG2,
}


def _codec(obj: pikepdf.Object) -> Codec:
    filt = obj.get("/Filter")
    if filt is None:
        return Codec.RAW
    if isinstance(filt, pikepdf.Array):
        filt = filt[-1]  # last filter in a chain is the image codec
    return _FILTER_CODEC.get(str(filt), Codec.RAW)


def _kind(obj: pikepdf.Object) -> ImageKind:
    if int(obj.get("/BitsPerComponent", 8)) == 1:
        return ImageKind.BITONAL
    return _CS_KIND.get(str(obj.get("/ColorSpace")), ImageKind.COLOR)


class PikepdfInspector(PdfInspector):
    def inspect(self, source: MediaFile) -> DocumentCensus:
        images: list[EmbeddedImage] = []
        image_bytes = 0
        with pikepdf.open(source.path) as pdf:
            for pno, page in enumerate(pdf.pages):
                box = page.mediabox
                page_w_in = (float(box[2]) - float(box[0])) / 72.0
                page_h_in = (float(box[3]) - float(box[1])) / 72.0
                for _, obj in page.get_images().items():
                    w, h = int(obj.Width), int(obj.Height)
                    with contextlib.suppress(pikepdf.PdfError):
                        image_bytes += int(obj.get("/Length", 0))
                    images.append(
                        EmbeddedImage(
                            xref=obj.objgen[0],
                            page_index=pno,
                            width=w,
                            height=h,
                            kind=_kind(obj),
                            codec=_codec(obj),
                            effective_dpi=EffectiveDpi(pixels=w, rendered_inches=page_w_in or 1.0),
                            rendered_area_sqin=(page_w_in * page_h_in) or 1.0,
                        )
                    )
            page_count = len(pdf.pages)
        return DocumentCensus(
            file=source,
            page_count=page_count,
            images=images,
            non_image_bytes=max(0, source.size_bytes - image_bytes),
        )
