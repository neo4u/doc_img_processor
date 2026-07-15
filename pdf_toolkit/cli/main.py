#!/usr/bin/env python3
"""pdf_toolkit CLI — inspect | compress | benchmark.

Examples:
    python -m pdf_toolkit.cli.main inspect ~/Downloads/oci_split
    python -m pdf_toolkit.cli.main compress in.pdf out.pdf --kb 1000
    python -m pdf_toolkit.cli.main benchmark ~/Downloads/oci_split ~/Downloads/oci_compare --kb 1000
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from pdf_toolkit.image_context.infrastructure.ssim_meter import NumpySsimMeter
from pdf_toolkit.pdf_context.application import CompressPdfToTarget, InspectDocument
from pdf_toolkit.pdf_context.domain import CompressionTarget
from pdf_toolkit.pdf_context.infrastructure.ghostscript_compressor import GhostscriptCompressor
from pdf_toolkit.pdf_context.infrastructure.agpl.native_compressor import NativeImageCompressor
from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
from pdf_toolkit.pdf_context.infrastructure.agpl.pymupdf_codec import PyMuPdfInspector
from pdf_toolkit.shared_kernel import ByteBudget, Metric, PerceptualScore, QualityFloor


def _target(kb: int, dpi_cap: int, floor: float) -> CompressionTarget:
    return CompressionTarget(
        budget=ByteBudget.kb(kb),
        quality_floor=QualityFloor(Metric.SSIM, floor),
        dpi_cap=dpi_cap,
    )


def cmd_inspect(args) -> None:
    inspect = InspectDocument(PyMuPdfInspector())
    root = Path(args.path)
    pdfs = sorted(root.glob("*.pdf")) if root.is_dir() else [root]
    print(f"{'file':<34}{'pg':>3}{'imgs':>5}{'kind':>10}{'codec':>7}{'eff.dpi':>8}{'img%':>6}")
    print("-" * 74)
    for pdf in pdfs:
        c = inspect(pdf)
        kinds = {i.kind.value for i in c.images}
        codecs = {i.codec.value for i in c.images}
        dpi = max((i.effective_dpi.value for i in c.images), default=0)
        print(f"{pdf.name:<34}{c.page_count:>3}{len(c.images):>5}"
              f"{'/'.join(kinds):>10}{'/'.join(codecs):>7}{dpi:>8.0f}"
              f"{100*c.image_bytes_fraction:>5.0f}%")


def cmd_compress(args) -> None:
    gs = GhostscriptCompressor()
    engines = {
        "pikepdf": PikepdfCompressor(escalation=gs),      # zero-AGPL default
        "pymupdf": NativeImageCompressor(escalation=gs),  # AGPL alternative
        "gs": gs,
    }
    engine = engines[args.engine]
    use = CompressPdfToTarget(engine)
    res = use(args.input, _target(args.kb, args.dpi_cap, args.floor), args.output)
    ssim = f"{res.score.value:.4f}" if res.score else "n/a"
    print(f"{engine.name}: {res.before_bytes//1000}KB -> {res.after_bytes//1000}KB "
          f"({res.saved_pct:.0f}% off) dpi={res.dpi_used} q={res.quality_used} "
          f"ssim={ssim} {res.elapsed_ms}ms{' [escalated]' if res.escalated else ''}")


def cmd_merge(args) -> None:
    import pikepdf
    inputs = [Path(p) for p in args.inputs]
    output = Path(args.output)
    merged = pikepdf.Pdf.new()
    for src in inputs:
        with pikepdf.open(src) as pdf:
            merged.pages.extend(pdf.pages)
    merged.save(output)
    total_pages = len(merged.pages)
    size_kb = output.stat().st_size // 1000
    print(f"merged {len(inputs)} files → {output.name}  ({total_pages} pages, {size_kb} KB)")


def cmd_benchmark(args) -> None:
    """Run every engine on every file into out_dir/<engine>/, score SSIM, tabulate."""
    src_dir = Path(args.src)
    out_dir = Path(args.out)
    pdfs = sorted(src_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"no PDFs in {src_dir}")

    gs = GhostscriptCompressor()
    engines = {
        "pikepdf": PikepdfCompressor(escalation=gs),      # zero-AGPL, license-clean
        "pymupdf": NativeImageCompressor(escalation=gs),  # AGPL alternative
        "ghostscript": gs,                                # escalation / baseline
    }
    meter = NumpySsimMeter()
    target = _target(args.kb, args.dpi_cap, args.floor)
    rows = []

    for name, engine in engines.items():
        (out_dir / name).mkdir(parents=True, exist_ok=True)
        for pdf in pdfs:
            out = out_dir / name / pdf.name
            use = CompressPdfToTarget(engine)
            res = use(pdf, target, out)
            # score whole-doc SSIM by rendering page 1 of src vs out for a fair compare
            ssim = _page_ssim(pdf, out, meter)
            rows.append({
                "engine": name, "file": pdf.name,
                "before_kb": res.before_bytes // 1000,
                "after_kb": res.after_bytes // 1000,
                "saved_pct": round(res.saved_pct, 1),
                "under_target": res.after_bytes <= target.budget.ceiling(),
                "dpi": res.dpi_used, "quality": res.quality_used,
                "ssim": round(ssim, 4), "ms": res.elapsed_ms,
                "escalated": res.escalated,
            })

    _print_table(rows, args.kb)
    csv_path = out_dir / "benchmark.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (out_dir / "benchmark.json").write_text(json.dumps(rows, indent=2))
    print(f"\nwrote {csv_path}")
    print(f"outputs: {out_dir}/<engine>/")


def _page_ssim(src_pdf: Path, out_pdf: Path, meter: NumpySsimMeter) -> float:
    """Render page 1 of each at a common size and compare — a whole-page quality proxy.

    Uses pypdfium2 (BSD/Apache) so the analysis harness is itself zero-AGPL.
    """
    import pypdfium2 as pdfium

    def png(p: Path) -> bytes:
        doc = pdfium.PdfDocument(str(p))
        try:
            bitmap = doc[0].render(scale=150 / 72)
            import io
            buf = io.BytesIO()
            bitmap.to_pil().save(buf, format="PNG")
            return buf.getvalue()
        finally:
            doc.close()
    try:
        return meter.score(png(src_pdf), png(out_pdf)).value
    except Exception:
        return float("nan")


def _print_table(rows: list[dict], kb: int) -> None:
    print(f"\nTarget: < {kb} KB   (✓ = under target ceiling)\n")
    print(f"{'engine':<12}{'file':<32}{'after':>7}{'saved':>7}{'✓':>3}{'ssim':>8}{'ms':>7}")
    print("-" * 78)
    for r in sorted(rows, key=lambda x: (x["file"], x["engine"])):
        ok = "✓" if r["under_target"] else "✗"
        esc = "*" if r["escalated"] else ""
        print(f"{r['engine']+esc:<12}{r['file']:<32}{r['after_kb']:>6}K"
              f"{r['saved_pct']:>6.0f}%{ok:>3}{r['ssim']:>8.4f}{r['ms']:>7}")


def main() -> None:
    p = argparse.ArgumentParser(prog="pdf_toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect"); pi.add_argument("path"); pi.set_defaults(fn=cmd_inspect)

    pc = sub.add_parser("compress")
    pc.add_argument("input"); pc.add_argument("output")
    pc.add_argument("--kb", type=int, default=1000)
    pc.add_argument("--dpi-cap", type=int, default=200)
    pc.add_argument("--floor", type=float, default=0.90)
    pc.add_argument("--engine", choices=["pikepdf", "pymupdf", "gs"], default="pikepdf")
    pc.set_defaults(fn=cmd_compress)

    pm = sub.add_parser("merge")
    pm.add_argument("inputs", nargs="+"); pm.add_argument("--output", required=True)
    pm.set_defaults(fn=cmd_merge)

    pb = sub.add_parser("benchmark")
    pb.add_argument("src"); pb.add_argument("out")
    pb.add_argument("--kb", type=int, default=1000)
    pb.add_argument("--dpi-cap", type=int, default=200)
    pb.add_argument("--floor", type=float, default=0.90)
    pb.set_defaults(fn=cmd_benchmark)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
