"""pdf context — pikepdf adapter for the PdfMerger port (MPL-2.0, license-clean)."""

from __future__ import annotations

from pathlib import Path

import pikepdf

from pdf_toolkit.shared_kernel import MediaFile


class PikepdfMerger:
    name = "pikepdf-merge"

    def merge(self, sources: list[MediaFile], out: Path) -> tuple[MediaFile, int]:
        merged = pikepdf.Pdf.new()
        for src in sources:
            with pikepdf.open(src.path) as pdf:
                merged.pages.extend(pdf.pages)
        merged.save(out)
        return MediaFile.of(out), len(merged.pages)
