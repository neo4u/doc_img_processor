"""PikepdfCompressor orchestration: short-circuit, hard rule #1, escalation (W4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf_toolkit.pdf_context.domain import CompressionResult
from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
from pdf_toolkit.pdf_context.ports import Compressor
from pdf_toolkit.shared_kernel import (
    ByteBudget,
    CompressionTarget,
    MediaFile,
    Metric,
    QualityFloor,
    UnreadableDocument,
)


class StubEscalation(Compressor):
    """Records whether escalation fired; writes a tiny valid output."""

    name = "stub-gs"

    def __init__(self) -> None:
        self.called = False

    def compress(self, source: MediaFile, target: CompressionTarget, out: Path) -> CompressionResult:
        self.called = True
        out.write_bytes(b"%PDF-1.4 stub escalated")
        return CompressionResult(
            output=MediaFile.of(out),
            engine=self.name,
            before_bytes=source.size_bytes,
            after_bytes=out.stat().st_size,
            dpi_used=72,
            quality_used=20,
            score=None,
            elapsed_ms=1,
            escalated=False,
        )


def _target(kb: int) -> CompressionTarget:
    return CompressionTarget(budget=ByteBudget.kb(kb), quality_floor=QualityFloor(Metric.SSIM, 0.0))


def test_under_ceiling_short_circuits_but_validates(scan_pdf, tmp_path):
    """Already under target → byte-identical copy, no image surgery."""
    out = tmp_path / "out.pdf"
    res = PikepdfCompressor().compress(MediaFile.of(scan_pdf), _target(100_000), out)
    assert out.read_bytes() == scan_pdf.read_bytes()
    assert res.after_bytes == res.before_bytes and not res.escalated


def test_passthrough_rejects_garbage(tmp_path):
    junk = tmp_path / "junk.pdf"
    junk.write_bytes(b"not a pdf")
    with pytest.raises(UnreadableDocument):
        PikepdfCompressor().compress(MediaFile.of(junk), _target(100_000), tmp_path / "o.pdf")


def test_compress_shrinks_and_never_enlarges(scan_pdf, tmp_path):
    """Real path: tight-but-reachable budget → smaller output (hard rule #1 bound)."""
    before = scan_pdf.stat().st_size
    out = tmp_path / "out.pdf"
    res = PikepdfCompressor().compress(MediaFile.of(scan_pdf), _target(max(20, before // 2000)), out)
    assert res.after_bytes <= before  # hard rule #1: never larger


def test_budget_miss_escalates_to_fallback(scan_pdf, tmp_path):
    """Impossible budget (1 KB) → BudgetMissed → escalation engine fires."""
    stub = StubEscalation()
    out = tmp_path / "out.pdf"
    res = PikepdfCompressor(escalation=stub).compress(MediaFile.of(scan_pdf), _target(1), out)
    assert stub.called
    assert res.escalated
    assert res.engine == "pikepdf->stub-gs"


def test_no_escalation_engine_reports_honestly(scan_pdf, tmp_path):
    """Impossible budget, no fallback → result over ceiling, escalated=False (no lying)."""
    out = tmp_path / "out.pdf"
    res = PikepdfCompressor().compress(MediaFile.of(scan_pdf), _target(1), out)
    assert res.after_bytes > 1000  # missed, visibly
    assert not res.escalated


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
