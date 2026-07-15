"""pdf context — application use cases. These double as NL tool schemas later."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pdf_toolkit.pdf_context.domain import CompressionResult, DocumentCensus
from pdf_toolkit.pdf_context.ports import Compressor, PdfInspector
from pdf_toolkit.shared_kernel import CompressionTarget, MediaFile


@dataclass
class InspectDocument:
    inspector: PdfInspector

    def __call__(self, path: str | Path) -> DocumentCensus:
        source = MediaFile.of(path)
        if not source.exists:
            raise FileNotFoundError(source.path)
        return self.inspector.inspect(source)


class PdfMerger(Protocol):
    """Port: concatenate PDFs in order."""

    def merge(self, sources: list[MediaFile], out: Path) -> tuple[MediaFile, int]:
        """Returns (merged file, page count)."""
        ...


@dataclass
class MergePdfs:
    merger: PdfMerger

    def __call__(self, paths: list[str | Path], out: str | Path) -> tuple[MediaFile, int]:
        sources = [MediaFile.of(p) for p in paths]
        for s in sources:
            if not s.exists:
                raise FileNotFoundError(f"file not found: {s.path}")
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return self.merger.merge(sources, out_path)


class StructuralOptimizer(Protocol):
    """Port: lossless PDF shrink — page rasters must stay byte-identical.

    Protocol (not ABC) so infrastructure adapters satisfy it structurally without
    importing the application layer; keeps the dependency arrow pointing inward.
    """

    name: str

    def optimize(self, source: MediaFile, out: Path, strip_metadata: bool = False): ...


@dataclass
class CompressPdfLossless:
    """Structural-only shrink: page rasters byte-identical (see pikepdf_lossless)."""

    optimizer: StructuralOptimizer

    def __call__(self, path: str | Path, out: str | Path, strip_metadata: bool = False):
        source = MediaFile.of(path)
        if not source.exists:
            raise FileNotFoundError(f"file not found: {source.path}")
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return self.optimizer.optimize(source, out_path, strip_metadata=strip_metadata)


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
