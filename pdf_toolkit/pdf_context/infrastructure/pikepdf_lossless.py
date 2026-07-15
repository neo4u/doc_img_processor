"""pdf context — lossless structural optimizer (pikepdf, MPL-2.0 — license-clean).

Structural only: unreferenced-object GC, object-stream packing, flate recompression.
Image streams are never re-encoded, so page rasters are byte-identical.
"""

from __future__ import annotations

from pathlib import Path

import pikepdf

from pdf_toolkit.shared_kernel import LosslessOutcome, MediaFile


class PikepdfStructuralOptimizer:
    name = "pikepdf-lossless"

    def optimize(self, source: MediaFile, out: Path, strip_metadata: bool = False) -> LosslessOutcome:
        with pikepdf.open(source.path) as pdf:
            if strip_metadata:
                # XMP + doc info only — content untouched (opt-in: changes file hash lineage)
                if "/Metadata" in pdf.Root:
                    del pdf.Root.Metadata
                with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                    meta.clear()
                if pdf.trailer.get("/Info") is not None:
                    del pdf.trailer.Info
            pdf.save(
                out,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                compress_streams=True,
                recompress_flate=True,
            )

        before = source.size_bytes
        after = out.stat().st_size
        if after >= before:  # hard rule #1
            out.write_bytes(source.path.read_bytes())
            return LosslessOutcome(MediaFile.of(out), before, before, changed=False)
        return LosslessOutcome(MediaFile.of(out), before, after, changed=True)
