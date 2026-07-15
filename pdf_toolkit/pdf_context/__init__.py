from pdf_toolkit.pdf_context.application import CompressPdfToTarget, InspectDocument
from pdf_toolkit.pdf_context.domain import (
    BudgetMissed,
    Codec,
    CompressionAttempted,
    CompressionRecipe,
    CompressionResult,
    CompressionTarget,
    DocumentCensus,
    EmbeddedImage,
    ImageKind,
    PageRange,
    QualityFloorViolated,
    ResampleFilter,
    SplitSpec,
)
from pdf_toolkit.pdf_context.ports import Compressor, PdfCodec, PdfInspector
from pdf_toolkit.pdf_context.services import BudgetDecomposition, TargetSizeSearch
