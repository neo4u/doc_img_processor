from pdf_toolkit.pdf_context.application import (
    CompressPdfLossless,
    CompressPdfToTarget,
    InspectDocument,
    MergePdfs,
)
from pdf_toolkit.pdf_context.domain import Codec, CompressionResult, DocumentCensus, EmbeddedImage
from pdf_toolkit.pdf_context.ports import Compressor, PdfInspector
from pdf_toolkit.pdf_context.services import BudgetDecomposition
