"""Ghostscript adapter: W3 timeout + stderr-surfacing contracts (mocked subprocess)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import pdf_toolkit.pdf_context.infrastructure.ghostscript_compressor as gsmod
from pdf_toolkit.shared_kernel import UnreadableDocument


def test_run_passes_timeout(monkeypatch, tmp_path):
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        (tmp_path / "out.pdf").write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(gsmod.subprocess, "run", fake_run)
    gs = gsmod.GhostscriptCompressor()
    gs._run(Path("/in.pdf"), tmp_path / "out.pdf", 150)
    assert captured["timeout"] == gsmod.SUBPROCESS_TIMEOUT_S  # never hang forever


def test_timeout_becomes_typed_error(monkeypatch, tmp_path):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

    monkeypatch.setattr(gsmod.subprocess, "run", fake_run)
    with pytest.raises(UnreadableDocument, match="timed out"):
        gsmod.GhostscriptCompressor()._run(Path("/in.pdf"), tmp_path / "o.pdf", 150)


def test_failure_surfaces_stderr_tail(monkeypatch, tmp_path):
    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr=b"GPL Ghostscript: some awful parse error")

    monkeypatch.setattr(gsmod.subprocess, "run", fake_run)
    with pytest.raises(UnreadableDocument, match="awful parse error"):
        gsmod.GhostscriptCompressor()._run(Path("/in.pdf"), tmp_path / "o.pdf", 150)


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
