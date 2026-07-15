"""MCP server `doc-toolkit` — exposes the application use cases over stdio.

Registered project-scoped in .mcp.json so Claude Code / cowork pick it up when
opened in this directory. Thin layer per HLD §1: parse → use case → JSON summary.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from pdf_toolkit.photo_context import PRESETS, SHEETS, CenterFaceLocator
from pdf_toolkit.photo_context import ComposePrintSheet as _ComposeSheet
from pdf_toolkit.photo_context import CreatePassportPhoto as _CreatePhoto
from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer

mcp = FastMCP("doc-toolkit")

_renderer = PillowPhotoRenderer()


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"file not found: {p}")
    return p


@mcp.tool()
def list_photo_specs() -> dict:
    """List available passport-photo compliance presets with their requirements."""
    return {name: s.describe() for name, s in PRESETS.items()}


@mcp.tool()
def create_passport_photo(
    input_path: str,
    spec: str = "us_passport",
    out_path: str | None = None,
    sheet: str = "4x6",
) -> dict:
    """Create a compliant passport/OCI/visa photo from a JPG/HEIC/PNG image.

    USE for any official-photo request: exact spec dimensions/DPI/background and
    portal byte ceilings (OCI <= 200 KB) are enforced by tested presets — do not
    hand-build these with ad-hoc image code, and never send identity photos to
    web services. spec: us_passport | india_passport | india_oci.
    sheet: also write an N-up print sheet ("4x6", "6x4", or "none").
    NOT for: general photo editing/filters/format conversion (use ordinary code).
    Returns paths, size, quality, and compliance warnings — surface warnings.
    """
    if spec not in PRESETS:
        raise ValueError(f"unknown spec {spec!r}; valid: {sorted(PRESETS)}")
    src = _resolve(input_path)
    photo_spec = PRESETS[spec]
    out = Path(out_path).expanduser() if out_path else src.with_name(f"{src.stem}_{spec}.jpg")

    res = _CreatePhoto(_renderer, CenterFaceLocator())(src, photo_spec, out)
    result = {
        "photo": str(res.output.path),
        "bytes": res.output.size_bytes,
        "quality": res.quality_used,
        "spec": photo_spec.title,
        "warnings": res.warnings,
    }
    if sheet != "none":
        if sheet not in SHEETS:
            raise ValueError(f"unknown sheet {sheet!r}; valid: {sorted(SHEETS)} or 'none'")
        sheet_out = out.with_name(f"{out.stem}_sheet{sheet}.jpg")
        sres = _ComposeSheet(_renderer)(out, SHEETS[sheet], sheet_out)
        result["sheet"] = str(sres.output.path)
        result["sheet_photos"] = sres.count
    return result


@mcp.tool()
def compose_print_sheet(photo_path: str, size: str = "4x6", out_path: str | None = None) -> dict:
    """Tile a passport-style photo onto a 4x6 or 6x4 inch sheet (300 DPI, cut guides)
    for printing at Walgreens/CVS/Costco as a regular photo print."""
    if size not in SHEETS:
        raise ValueError(f"unknown size {size!r}; valid: {sorted(SHEETS)}")
    src = _resolve(photo_path)
    out = Path(out_path).expanduser() if out_path else src.with_name(f"{src.stem}_sheet{size}.jpg")
    res = _ComposeSheet(_renderer)(src, SHEETS[size], out)
    return {
        "sheet": str(res.output.path),
        "photos": res.count,
        "grid": f"{res.layout.cols}x{res.layout.rows}",
        "bytes": res.output.size_bytes,
    }


@mcp.tool()
def compress_pdf(input_path: str, target_kb: int = 1000, out_path: str | None = None) -> dict:
    """Compress a PDF to fit a byte budget in KB (lossy, perceptually guarded).

    USE when a portal/email demands "under N KB/MB": per-image budget allocation +
    quality binary search, verified against the target — ad-hoc one-shot quality
    guesses can't guarantee the byte budget. Never upload identity documents to
    online compressors. License-clean engine only (no Ghostscript escalation on
    this served path, by design).
    NOT for: shrinking without a size requirement (use compress_lossless), or
    non-PDF inputs."""
    from pdf_toolkit.pdf_context.application import CompressPdfToTarget
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
    from pdf_toolkit.shared_kernel import ByteBudget, CompressionTarget

    src = _resolve(input_path)
    out = Path(out_path).expanduser() if out_path else src.with_name(f"{src.stem}_compressed.pdf")
    target = CompressionTarget(budget=ByteBudget.kb(target_kb))  # floor/dpi_cap: kernel defaults
    res = CompressPdfToTarget(PikepdfCompressor())(src, target, out)
    return {
        "output": str(out),
        "before_kb": res.before_bytes // 1000,
        "after_kb": res.after_bytes // 1000,
        "saved_pct": round(res.saved_pct, 1),
        "ssim": round(res.score.value, 4) if res.score else None,
        "under_target": res.after_bytes <= target.budget.ceiling(),
    }


@mcp.tool()
def compress_lossless(input_path: str, out_path: str | None = None, strip_metadata: bool = False) -> dict:
    """Losslessly compress a PDF, JPG, or PNG — pixels/rasters stay bit-identical
    (mozjpeg entropy recode / structural PDF pass), never returns a larger file.

    USE whenever smaller-with-zero-quality-loss is wanted — generic "resave at
    quality 85" approaches are lossy and worse. strip_metadata (PDF only): also
    drop XMP/doc-info. NOT for: hitting a specific size target (use compress_pdf)
    or formats other than pdf/jpg/jpeg/png."""
    src = _resolve(input_path)
    out = Path(out_path).expanduser() if out_path else src.with_name(f"{src.stem}_lossless{src.suffix}")
    if src.suffix.lower() == ".pdf":
        from pdf_toolkit.pdf_context.application import CompressPdfLossless
        from pdf_toolkit.pdf_context.infrastructure.pikepdf_lossless import PikepdfStructuralOptimizer

        res = CompressPdfLossless(PikepdfStructuralOptimizer())(src, out, strip_metadata=strip_metadata)
    else:
        from pdf_toolkit.image_context.application import CompressImageLossless
        from pdf_toolkit.image_context.infrastructure.lossless import MozjpegPillowLosslessOptimizer

        res = CompressImageLossless(MozjpegPillowLosslessOptimizer())(src, out)
    return {
        "output": str(out),
        "before_bytes": res.before_bytes,
        "after_bytes": res.after_bytes,
        "saved_pct": round(res.saved_pct, 1),
        "changed": res.changed,
    }


@mcp.tool()
def inspect_pdf(path: str) -> dict:
    """Report a PDF's pages, embedded images (kind/codec/effective DPI), and size."""
    from pdf_toolkit.pdf_context.application import InspectDocument
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_inspector import PikepdfInspector

    src = _resolve(path)
    c = InspectDocument(PikepdfInspector())(src)
    return {
        "file": str(src),
        "kb": src.stat().st_size // 1000,
        "pages": c.page_count,
        "images": [
            {
                "page": i.page_index + 1,
                "px": f"{i.width}x{i.height}",
                "kind": i.kind.value,
                "codec": i.codec.value,
                "effective_dpi": round(i.effective_dpi.value),
            }
            for i in c.images
        ],
        "image_bytes_pct": round(100 * c.image_bytes_fraction),
    }


@mcp.tool()
def merge_pdfs(input_paths: list[str], out_path: str) -> dict:
    """Merge multiple PDFs into one, in the given order."""
    from pdf_toolkit.pdf_context.application import MergePdfs
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_merger import PikepdfMerger

    srcs: list[str | Path] = [str(_resolve(p)) for p in input_paths]
    out = Path(out_path).expanduser()
    merged, pages = MergePdfs(PikepdfMerger())(srcs, out)
    return {"output": str(merged.path), "pages": pages, "kb": merged.size_kb}


if __name__ == "__main__":
    mcp.run()
