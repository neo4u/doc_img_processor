"""pdf context — ports (interfaces). Adapters in infrastructure/ implement these."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdf_toolkit.pdf_context.domain import (
    Codec,
    CompressionResult,
    CompressionTarget,
    DocumentCensus,
    SplitSpec,
)
from pdf_toolkit.shared_kernel import MediaFile


class Splitter(ABC):
    @abstractmethod
    def split(self, source: MediaFile, specs: list[SplitSpec], out_dir: Path) -> list[MediaFile]:
        ...


class PdfInspector(ABC):
    @abstractmethod
    def inspect(self, source: MediaFile) -> DocumentCensus:
        ...


class PdfCodec(ABC):
    """Low-level image surgery + structural optimization on a PDF."""

    @abstractmethod
    def extract_image(self, source: MediaFile, xref: int) -> tuple[bytes, str]:
        """Return (raw image bytes, ext) for an xref."""

    @abstractmethod
    def replace_image(self, doc_handle, xref: int, new_bytes: bytes) -> None:
        ...

    @abstractmethod
    def structural_optimize(self, source: MediaFile, out: Path) -> MediaFile:
        """Lossless pass: gc, dedupe, deflate, strip metadata."""


class Compressor(ABC):
    """A whole-document compressor behind one port. GS, PyMuPDF, etc. all fit here."""

    name: str

    @abstractmethod
    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult:
        ...
