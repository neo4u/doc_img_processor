"""pdf context — Ghostscript adapter (the 'nuclear option' Compressor).

Binary-searches -dColorImageResolution to sit just under the byte budget. Confined
here so the external `gs` dependency is swappable. Fires as an escalation when the
native pipeline reports BudgetMissed.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path

from pdf_toolkit.pdf_context.domain import CompressionResult
from pdf_toolkit.pdf_context.ports import Compressor
from pdf_toolkit.shared_kernel import SUBPROCESS_TIMEOUT_S, CompressionTarget, MediaFile, UnreadableDocument


class GhostscriptCompressor(Compressor):
    name = "ghostscript"
    _ITERATIONS = 8

    def __init__(self, gs_binary: str = "gs") -> None:
        self._gs = gs_binary

    def _run(self, src: Path, dst: Path, dpi: int) -> int:
        cmd = [
            self._gs,
            "-sDEVICE=pdfwrite",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dPDFSETTINGS=/default",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={dpi}",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            f"-sOutputFile={dst}",
            str(src),
        ]
        try:
            # Timeout (W3): gs can hang forever on pathological input; stderr is
            # surfaced on failure so CalledProcessError is actionable.
            subprocess.run(cmd, check=True, capture_output=True, timeout=SUBPROCESS_TIMEOUT_S)
        except subprocess.TimeoutExpired as e:
            raise UnreadableDocument(
                f"ghostscript timed out after {SUBPROCESS_TIMEOUT_S}s on {src.name}"
            ) from e
        except subprocess.CalledProcessError as e:
            tail = (e.stderr or b"").decode(errors="replace").strip()[-500:]
            raise UnreadableDocument(f"ghostscript failed on {src.name}: {tail}") from e
        return dst.stat().st_size

    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult:
        start = time.monotonic()
        ceiling = target.budget.ceiling()

        if source.size_bytes <= ceiling:
            out.write_bytes(source.path.read_bytes())
            return self._result(source, out, dpi=0, start=start)

        low, high = target.dpi_range
        best_dpi = low
        with tempfile.TemporaryDirectory() as tmp:
            for _ in range(self._ITERATIONS):
                mid = (low + high) // 2
                probe = Path(tmp) / "p.pdf"
                if self._run(source.path, probe, mid) <= ceiling:
                    best_dpi = mid
                    low = mid
                else:
                    high = mid

        self._run(source.path, out, best_dpi)
        # Hard rule #1: never emit larger than input.
        if out.stat().st_size >= source.size_bytes:
            out.write_bytes(source.path.read_bytes())
            best_dpi = 0
        return self._result(source, out, dpi=best_dpi, start=start)

    def _result(self, source: MediaFile, out: Path, dpi: int, start: float) -> CompressionResult:
        return CompressionResult(
            output=MediaFile.of(out),
            engine=self.name,
            before_bytes=source.size_bytes,
            after_bytes=out.stat().st_size,
            dpi_used=dpi,
            quality_used=0,
            score=None,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            escalated=False,
        )
