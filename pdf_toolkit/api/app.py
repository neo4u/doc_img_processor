"""HTTP API — thin layer over the application use cases (HLD §3).

Run:  .venv/bin/uvicorn pdf_toolkit.api.app:app --port 8080
Uploads are processed in a per-request tempdir and deleted after the response (N1).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import python_multipart  # noqa: F401 — fastapi needs it at runtime for multipart; import makes gazelle wire the dep
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

from pdf_toolkit.photo_context import (
    PRESETS,
    SHEETS,
    CenterFaceLocator,
    ComposePrintSheet,
    CreatePassportPhoto,
)
from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer

app = FastAPI(title="doc-toolkit", version="1.0")

_renderer = PillowPhotoRenderer()


def _save_upload(file: UploadFile, workdir: Path) -> Path:
    suffix = Path(file.filename or "upload").suffix or ".bin"
    dst = workdir / f"input{suffix}"
    with dst.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return dst


def _workdir(background: BackgroundTasks) -> Path:
    work = Path(tempfile.mkdtemp(prefix="doc_toolkit_"))
    background.add_task(shutil.rmtree, work, ignore_errors=True)  # N1: clean up
    return work


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/specs")
def specs() -> dict[str, dict[str, object]]:
    return {name: s.describe() for name, s in PRESETS.items()}


@app.post("/photo")
def photo(file: UploadFile, background: BackgroundTasks, spec: str = "us_passport") -> FileResponse:
    if spec not in PRESETS:
        raise HTTPException(422, f"unknown spec {spec!r}; valid: {sorted(PRESETS)}")
    work = _workdir(background)
    src = _save_upload(file, work)
    out = work / f"{Path(file.filename or 'photo').stem}_{spec}.jpg"
    try:
        res = CreatePassportPhoto(_renderer, CenterFaceLocator())(src, PRESETS[spec], out)
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return FileResponse(
        out,
        media_type="image/jpeg",
        filename=out.name,
        headers={"X-Quality": str(res.quality_used), "X-Warnings": " | ".join(res.warnings)},
    )


@app.post("/sheet")
def sheet(file: UploadFile, background: BackgroundTasks, size: str = "4x6") -> FileResponse:
    if size not in SHEETS:
        raise HTTPException(422, f"unknown size {size!r}; valid: {sorted(SHEETS)}")
    work = _workdir(background)
    src = _save_upload(file, work)
    out = work / f"{Path(file.filename or 'photo').stem}_sheet{size}.jpg"
    try:
        res = ComposePrintSheet(_renderer)(src, SHEETS[size], out)
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return FileResponse(out, media_type="image/jpeg", filename=out.name, headers={"X-Photos": str(res.count)})


@app.post("/compress/target")
def compress_target(file: UploadFile, background: BackgroundTasks, kb: int = 1000) -> FileResponse:
    from pdf_toolkit.pdf_context.application import CompressPdfToTarget
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_compressor import PikepdfCompressor
    from pdf_toolkit.shared_kernel import ByteBudget, CompressionTarget

    work = _workdir(background)
    src = _save_upload(file, work)
    out = work / f"{Path(file.filename or 'doc').stem}_compressed.pdf"
    target = CompressionTarget(budget=ByteBudget.kb(kb))  # floor/dpi_cap: kernel defaults
    try:
        res = CompressPdfToTarget(PikepdfCompressor())(src, target, out)
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return FileResponse(
        out,
        media_type="application/pdf",
        filename=out.name,
        headers={"X-Before-Bytes": str(res.before_bytes), "X-After-Bytes": str(res.after_bytes)},
    )


@app.post("/inspect")
def inspect(file: UploadFile, background: BackgroundTasks) -> dict[str, object]:
    from pdf_toolkit.pdf_context.application import InspectDocument
    from pdf_toolkit.pdf_context.infrastructure.pikepdf_inspector import PikepdfInspector

    work = _workdir(background)
    src = _save_upload(file, work)
    try:
        c = InspectDocument(PikepdfInspector())(src)
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return {
        "pages": c.page_count,
        "kb": src.stat().st_size // 1000,
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


@app.post("/compress/lossless")
def compress_lossless(
    file: UploadFile, background: BackgroundTasks, strip_metadata: bool = False
) -> FileResponse:
    work = _workdir(background)
    src = _save_upload(file, work)
    out = work / f"{src.stem}_lossless{src.suffix}"
    try:
        if src.suffix.lower() == ".pdf":
            from pdf_toolkit.pdf_context.application import CompressPdfLossless
            from pdf_toolkit.pdf_context.infrastructure.pikepdf_lossless import PikepdfStructuralOptimizer

            res = CompressPdfLossless(PikepdfStructuralOptimizer())(src, out, strip_metadata=strip_metadata)
            media = "application/pdf"
        else:
            from pdf_toolkit.image_context.application import CompressImageLossless
            from pdf_toolkit.image_context.infrastructure.lossless import MozjpegPillowLosslessOptimizer

            res = CompressImageLossless(MozjpegPillowLosslessOptimizer())(src, out)
            media = "image/jpeg" if src.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return FileResponse(
        out,
        media_type=media,
        filename=f"{Path(file.filename or 'file').stem}_lossless{src.suffix}",
        headers={
            "X-Before-Bytes": str(res.before_bytes),
            "X-After-Bytes": str(res.after_bytes),
            "X-Changed": str(res.changed).lower(),
        },
    )
