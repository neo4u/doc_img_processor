"""HTTP API — thin layer over the application use cases (HLD §3).

Run:  .venv/bin/uvicorn pdf_toolkit.api.app:app --port 8080
Uploads are processed in a per-request tempdir and deleted after the response (N1).
Hardening (W3): upload cap → 413, typed errors → 422, correlation-id + logged 500s.
Endpoints stay sync `def` on purpose — Starlette runs them in a threadpool; an
`async def` refactor would move CPU work onto the event loop (see docs/RESEARCH.md §4).
"""

from __future__ import annotations

import shutil
import tempfile
import time
import uuid
from pathlib import Path

import python_multipart  # noqa: F401 — fastapi needs it at runtime for multipart; import makes gazelle wire the dep
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from pdf_toolkit.photo_context import (
    PRESETS,
    SHEETS,
    CenterFaceLocator,
    ComposePrintSheet,
    CreatePassportPhoto,
)
from pdf_toolkit.photo_context.infrastructure.pillow_renderer import PillowPhotoRenderer
from pdf_toolkit.shared_kernel import MAX_UPLOAD_BYTES, InvalidInput, get_logger

app = FastAPI(title="doc-toolkit", version="1.0")

_renderer = PillowPhotoRenderer()
_log = get_logger(__name__)

_COPY_CHUNK = 1 << 20  # 1 MiB


@app.middleware("http")
async def _observe(request: Request, call_next):
    """Correlation id (echoed or minted) + one log line per request (W3)."""
    cid = request.headers.get("X-Correlation-Id") or uuid.uuid4().hex[:12]
    request.state.cid = cid
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = cid
    _log.info(
        "cid=%s %s %s -> %s in %dms",
        cid,
        request.method,
        request.url.path,
        response.status_code,
        int((time.monotonic() - started) * 1000),
    )
    return response


@app.exception_handler(InvalidInput)
async def _invalid_input(request: Request, exc: InvalidInput) -> JSONResponse:
    # Covers UnreadableDocument too (subclass): the user can fix these → 422.
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    cid = getattr(request.state, "cid", "?")
    _log.exception("cid=%s unhandled error on %s: %s", cid, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": f"internal error (cid={cid})"})


def _save_upload(file: UploadFile, workdir: Path) -> Path:
    """Counted chunked copy — enforce MAX_UPLOAD_BYTES even when Content-Length lies."""
    declared = getattr(file, "size", None)
    if declared is not None and declared > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"upload is {declared} bytes; cap is {MAX_UPLOAD_BYTES}")
    suffix = Path(file.filename or "upload").suffix or ".bin"
    dst = workdir / f"input{suffix}"
    written = 0
    with dst.open("wb") as f:
        while chunk := file.file.read(_COPY_CHUNK):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                raise HTTPException(413, f"upload exceeds the {MAX_UPLOAD_BYTES}-byte cap")
            f.write(chunk)
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
    res = CreatePassportPhoto(_renderer, CenterFaceLocator())(src, PRESETS[spec], out)
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
    res = ComposePrintSheet(_renderer)(src, SHEETS[size], out)
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
    res = CompressPdfToTarget(PikepdfCompressor())(src, target, out)
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
    c = InspectDocument(PikepdfInspector())(src)
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
