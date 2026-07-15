"""pdf context — application use cases. These double as NL tool schemas later."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pdf_toolkit.pdf_context.domain import (
    CompressionResult,
    CompressionTarget,
    DocumentCensus,
)
from pdf_toolkit.pdf_context.ports import Compressor, PdfInspector
from pdf_toolkit.shared_kernel import MediaFile


@dataclass
class InspectDocument:
    inspector: PdfInspector

    def __call__(self, path: str | Path) -> DocumentCensus:
        source = MediaFile.of(path)
        if not source.exists:
            raise FileNotFoundError(source.path)
        return self.inspector.inspect(source)


@dataclass
class CompressPdfToTarget:
    compressor: Compressor

    def __call__(self, path: str | Path, target: CompressionTarget, out: str | Path) -> CompressionResult:
        source = MediaFile.of(path)
        if not source.exists:
            raise FileNotFoundError(source.path)
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return self.compressor.compress(source, target, out_path)
