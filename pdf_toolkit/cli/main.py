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
from pathlib import Path

from pdf_toolkit.image_context.infrastructure.ssim_meter import NumpySsimMeter
from pdf_toolkit.pdf_context.application import CompressPdfToTarget, InspectDocument
from pdf_toolkit.pdf_context.infrastructure.agpl.native_compressor import NativeImageCompressor
from pdf_toolkit.pdf_context.infrastructure.agpl.pymupdf_codec import PyMuPdfInspector
from pdf_toolkit.pdf_context.infrastructure.ghostscript_compressor import GhostscriptCompressor
from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
from pdf_toolkit.photo_context.domain import SHEETS
from pdf_toolkit.shared_kernel import (
    DEFAULT_TARGET_KB,
    ByteBudget,
    CompressionTarget,
    InvalidInput,
    Metric,
    QualityFloor,
)


def build_engines() -> dict[str, object]:
    """One engine registry (W2): canonical ids, shared by compress and benchmark."""
    gs = GhostscriptCompressor()
    return {
        "pikepdf": PikepdfCompressor(escalation=gs),  # zero-AGPL default (+gs escalation, CLI-only)
        "pymupdf": NativeImageCompressor(escalation=gs),  # AGPL alternative
        "gs": gs,  # escalation / baseline
    }


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
        print(
            f"{pdf.name:<34}{c.page_count:>3}{len(c.images):>5}"
            f"{'/'.join(kinds):>10}{'/'.join(codecs):>7}{dpi:>8.0f}"
            f"{100 * c.image_bytes_fraction:>5.0f}%"
        )


def cmd_compress(args) -> None:
    gs = GhostscriptCompressor()
    engines = {
        "pikepdf": PikepdfCompressor(escalation=gs),  # zero-AGPL default
        "pymupdf": NativeImageCompressor(escalation=gs),  # AGPL alternative
        "gs": gs,
    }
    engine = engines[args.engine]
    use = CompressPdfToTarget(engine)
    res = use(args.input, _target(args.kb, args.dpi_cap, args.floor), args.output)
    ssim = f"{res.score.value:.4f}" if res.score else "n/a"
    print(
        f"{engine.name}: {res.before_bytes // 1000}KB -> {res.after_bytes // 1000}KB "
        f"({res.saved_pct:.0f}% off) dpi={res.dpi_used} q={res.quality_used} "
        f"ssim={ssim} {res.elapsed_ms}ms{' [escalated]' if res.escalated else ''}"
    )


def cmd_merge(args) -> None:
    from pdf_toolkit.pdf_context.application import MergePdfs
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_merger import PikepdfMerger

    merged, pages = MergePdfs(PikepdfMerger())(args.inputs, args.output)
    print(f"merged {len(args.inputs)} files → {merged.path.name}  ({pages} pages, {merged.size_kb} KB)")


def cmd_photo(args) -> None:
    from pdf_toolkit.photo_context import (
        PRESETS,
        SHEETS,
        CenterFaceLocator,
        ComposePrintSheet,
        CreatePassportPhoto,
    )
    from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer

    spec = PRESETS[args.spec]
    src = Path(args.input)
    out = Path(args.out) if args.out else src.with_name(f"{src.stem}_{spec.name}.jpg")

    renderer = PillowPhotoRenderer()
    res = CreatePassportPhoto(renderer, CenterFaceLocator())(src, spec, out)
    print(
        f"{spec.title}: {out.name}  {spec.width_px}×{spec.height_px}@{spec.dpi}dpi "
        f"{res.output.size_kb}KB q={res.quality_used}"
    )
    for w in res.warnings:
        print(f"  ⚠ {w}")

    if args.sheet != "none":
        sheet_spec = SHEETS[args.sheet]
        sheet_out = out.with_name(f"{out.stem}_sheet{args.sheet}.jpg")
        sres = ComposePrintSheet(renderer)(out, sheet_spec, sheet_out)
        print(
            f"print sheet: {sheet_out.name}  {sres.count}-up on {sheet_spec.name} in — "
            f"print at Walgreens/CVS as a standard {sheet_spec.name} photo, then cut"
        )


def cmd_sheet(args) -> None:
    from pdf_toolkit.photo_context import SHEETS, ComposePrintSheet
    from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer

    src = Path(args.photo)
    sheet_spec = SHEETS[args.size]
    out = Path(args.out) if args.out else src.with_name(f"{src.stem}_sheet{args.size}.jpg")
    res = ComposePrintSheet(PillowPhotoRenderer())(
        src, sheet_spec, out, photo_size_in=args.photo_in, guides=not args.no_guides
    )
    print(
        f"{out.name}: {res.count}-up ({res.layout.cols}×{res.layout.rows}) on "
        f"{sheet_spec.name} in @ {sheet_spec.dpi}dpi  {res.output.size_kb}KB"
    )


def cmd_lossless(args) -> None:
    src = Path(args.input)
    out = Path(args.out) if args.out else src.with_name(f"{src.stem}_lossless{src.suffix}")
    ext = src.suffix.lower()
    if ext == ".pdf":
        from pdf_toolkit.pdf_context.application import CompressPdfLossless
        from pdf_toolkit.pdf_context.infrastructure.pikepdf_lossless import PikepdfStructuralOptimizer

        res = CompressPdfLossless(PikepdfStructuralOptimizer())(src, out, strip_metadata=args.strip_metadata)
    else:
        from pdf_toolkit.image_context.application import CompressImageLossless
        from pdf_toolkit.image_context.infrastructure.lossless import MozjpegPillowLosslessOptimizer

        res = CompressImageLossless(MozjpegPillowLosslessOptimizer())(src, out)
    note = "" if res.changed else "  (already optimal — copied unchanged)"
    print(
        f"{out.name}: {res.before_bytes // 1000}KB -> {res.after_bytes // 1000}KB "
        f"({res.saved_pct:.1f}% off, lossless){note}"
    )


def cmd_benchmark(args) -> None:
    """Run every engine on every file into out_dir/<engine>/, score SSIM, tabulate."""
    src_dir = Path(args.src)
    out_dir = Path(args.out)
    pdfs = sorted(src_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"no PDFs in {src_dir}")

    gs = GhostscriptCompressor()
    engines = {
        "pikepdf": PikepdfCompressor(escalation=gs),  # zero-AGPL, license-clean
        "pymupdf": NativeImageCompressor(escalation=gs),  # AGPL alternative
        "ghostscript": gs,  # escalation / baseline
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
            rows.append(
                {
                    "engine": name,
                    "file": pdf.name,
                    "before_kb": res.before_bytes // 1000,
                    "after_kb": res.after_bytes // 1000,
                    "saved_pct": round(res.saved_pct, 1),
                    "under_target": res.after_bytes <= target.budget.ceiling(),
                    "dpi": res.dpi_used,
                    "quality": res.quality_used,
                    "ssim": round(ssim, 4),
                    "ms": res.elapsed_ms,
                    "escalated": res.escalated,
                }
            )

    _print_table(rows, args.kb)
    csv_path = out_dir / "benchmark.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
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
        print(
            f"{r['engine'] + esc:<12}{r['file']:<32}{r['after_kb']:>6}K"
            f"{r['saved_pct']:>6.0f}%{ok:>3}{r['ssim']:>8.4f}{r['ms']:>7}"
        )


def main() -> None:
    p = argparse.ArgumentParser(prog="pdf_toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect")
    pi.add_argument("path")
    pi.set_defaults(fn=cmd_inspect)

    pc = sub.add_parser("compress")
    pc.add_argument("input")
    pc.add_argument("output")
    pc.add_argument("--kb", type=int, default=DEFAULT_TARGET_KB)
    pc.add_argument("--dpi-cap", type=int, default=200)
    pc.add_argument("--floor", type=float, default=0.90)
    pc.add_argument("--engine", choices=sorted(build_engines()), default="pikepdf")
    pc.set_defaults(fn=cmd_compress)

    pm = sub.add_parser("merge")
    pm.add_argument("inputs", nargs="+")
    pm.add_argument("--output", required=True)
    pm.set_defaults(fn=cmd_merge)

    pp = sub.add_parser("photo", help="passport-style photo from JPG/HEIC")
    pp.add_argument("input")
    pp.add_argument("--spec", choices=["us_passport", "india_passport", "india_oci"], default="us_passport")
    pp.add_argument("--out", default=None)
    pp.add_argument(
        "--sheet",
        choices=["4x6", "6x4", "none"],
        default="4x6",
        help="also write an N-up print sheet (default 4x6)",
    )
    pp.set_defaults(fn=cmd_photo)

    ps = sub.add_parser("sheet", help="N-up print sheet from a passport-style photo")
    ps.add_argument("photo")
    ps.add_argument("--size", choices=sorted(SHEETS), default="4x6")
    ps.add_argument("--photo-in", type=float, default=2.0, help="printed photo edge in inches (default 2.0)")
    ps.add_argument("--out", default=None)
    ps.add_argument("--no-guides", action="store_true")
    ps.set_defaults(fn=cmd_sheet)

    pl = sub.add_parser("lossless", help="lossless compress: pdf, jpg, png")
    pl.add_argument("input")
    pl.add_argument("--out", default=None)
    pl.add_argument("--strip-metadata", action="store_true", help="PDF only: also drop XMP/doc-info metadata")
    pl.set_defaults(fn=cmd_lossless)

    pb = sub.add_parser("benchmark")
    pb.add_argument("src")
    pb.add_argument("out")
    pb.add_argument("--kb", type=int, default=DEFAULT_TARGET_KB)
    pb.add_argument("--dpi-cap", type=int, default=200)
    pb.add_argument("--floor", type=float, default=0.90)
    pb.set_defaults(fn=cmd_benchmark)

    args = p.parse_args()
    try:
        args.fn(args)
    except (InvalidInput, FileNotFoundError) as e:
        # Domain/user errors: message not traceback, exit 2 (LLD §Errors) —
        # the skills that shell out depend on this contract.
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
