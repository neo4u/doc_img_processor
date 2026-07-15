"""pdf context — ports (interfaces). Adapters in infrastructure/ implement these."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdf_toolkit.pdf_context.domain import CompressionResult, DocumentCensus
from pdf_toolkit.shared_kernel import CompressionTarget, MediaFile


class PdfInspector(ABC):
    @abstractmethod
    def inspect(self, source: MediaFile) -> DocumentCensus: ...


class Compressor(ABC):
    """A whole-document compressor behind one port. GS, PyMuPDF, etc. all fit here."""

    name: str

    @abstractmethod
    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult: ...
