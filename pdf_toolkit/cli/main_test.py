"""CLI e2e: argv → main() per subcommand, exit-code contract (W4)."""

from __future__ import annotations

import pytest

from pdf_toolkit.cli.main import main


def _run(monkeypatch, *argv: str) -> None:
    monkeypatch.setattr("sys.argv", ["pdf_toolkit", *argv])
    main()


def test_photo_writes_spec_output_and_sheet(monkeypatch, portrait, capsys):
    _run(monkeypatch, "photo", str(portrait), "--spec", "india_oci")
    out = capsys.readouterr().out
    assert "India OCI" in out and "600×600@300dpi" in out
    assert portrait.with_name("portrait_india_oci.jpg").exists()
    assert portrait.with_name("portrait_india_oci_sheet4x6.jpg").exists()


def test_photo_sheet_none_skips_sheet(monkeypatch, portrait):
    _run(monkeypatch, "photo", str(portrait), "--sheet", "none", "--out", str(portrait.with_name("p2.jpg")))
    assert portrait.with_name("p2.jpg").exists()
    assert not portrait.with_name("p2_sheet4x6.jpg").exists()


def test_sheet_landscape(monkeypatch, portrait, capsys):
    _run(monkeypatch, "photo", str(portrait), "--sheet", "none", "--out", str(portrait.with_name("p3.jpg")))
    _run(monkeypatch, "sheet", str(portrait.with_name("p3.jpg")), "--size", "6x4")
    assert "6-up (3×2)" in capsys.readouterr().out


def test_lossless_jpg(monkeypatch, portrait, capsys):
    _run(monkeypatch, "lossless", str(portrait))
    assert "lossless" in capsys.readouterr().out
    assert portrait.with_name("portrait_lossless.jpg").exists()


def test_merge(monkeypatch, scan_pdf, tmp_path, capsys):
    out = tmp_path / "merged.pdf"
    _run(monkeypatch, "merge", str(scan_pdf), str(scan_pdf), "--output", str(out))
    assert "6 pages" in capsys.readouterr().out  # 3 + 3


def test_missing_file_exits_2_with_message(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "lossless", "/nope/missing.pdf")
    assert exc.value.code == 2
    assert "error: file not found" in capsys.readouterr().err


def test_unknown_spec_rejected_by_argparse(monkeypatch, portrait):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "photo", str(portrait), "--spec", "mars_visa")
    assert exc.value.code == 2  # argparse's own exit code — same contract


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
