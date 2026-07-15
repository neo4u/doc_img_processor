# OS / CS / Algorithms — mental models used here

> One line of *why*, where it lives in the code, a link to go deep. Nothing else.

## Image & signal

| Mental model | Used at | Deep dive |
|---|---|---|
| **JPEG = one lossy stage.** RGB→YCbCr→DCT→quantize(*lossy*)→Huffman. Redo only the Huffman stage ⇒ smaller file, bit-identical pixels | `image_context/infrastructure/lossless.py` | [Wallace 1991, the JPEG paper](https://dl.acm.org/doi/10.1145/103085.103089) |
| **Chroma subsampling.** Eyes resolve luma ≫ chroma; 4:2:2 keeps color edges for inspection-grade photos | `pillow_renderer.encode_jpeg(subsampling=1)` | [Poynton, Chroma subsampling notes](https://poynton.ca/PDFs/Chroma_subsampling_notes.pdf) |
| **Resize = sampling theory.** Lanczos ≈ ideal low-pass (anti-alias); nearest only when interpolation is *wrong* (bitonal) | `ResampleFilter` in `pdf_context/domain.py` | [Turkowski, Filters for common resampling tasks](https://legacy.imagemagick.org/Usage/filter/Turkowski_1990.pdf) |
| **Otsu threshold.** Histogram valley → automatic binarization after gray downsample | bitonal branch, `DOMAIN.md` §algorithm | [Otsu 1979](https://ieeexplore.ieee.org/document/4310076) |
| **SSIM ≠ MSE.** Compare local structure, not pixels. But know its blind spots ↓ | `ssim_meter.py`, `TargetSizeSearch` | [Wang et al. 2004](https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf) |
| **A metric can be true and useless: calibration + pooling.** Global-mean luma SSIM 0.90 passes almost any JPEG (real floors sit at 0.999+); mean pooling lets clean background outvote a destroyed text line; luma-only is blind to chroma damage. Fix = better metric (SSIMULACRA2: XYB color, multi-scale, 4-norm pooling, human-anchored 0–100) not a tweaked threshold | RESEARCH §3; W6 `Ssimulacra2Meter` | [Understanding SSIM](https://arxiv.org/abs/2006.13846) · [SSIMULACRA2](https://github.com/cloudinary/ssimulacra2) |
| **Put the perceptual model inside the encoder.** jpegli's Butteraugli-driven adaptive quantization hits a *distance* (or byte target) directly — search-free; our binary search becomes the fallback, not the algorithm | W6 `JpegliCodec` (`cjpegli --target_size`) | [jpegli announcement](https://opensource.googleblog.com/2024/04/introducing-jpegli-new-jpeg-coding-library.html) |
| **Matting ≠ segmentation.** Segmentation = hard class mask; matting = per-pixel *alpha* (hair, glasses edges) — required for believable background replacement; then it's just Porter-Duff over white | W7 `BackgroundMatter` (MODNet) | [MODNet](https://github.com/ZHKKKe/MODNet) |
| **Landmarks → geometry, not magic.** 5 facial points give crop anchor (face center), roll (`atan2(eye_dy, eye_dx)`), and head-height compliance (crown-chin fraction vs spec band) — all affine math after one tiny ONNX model | W7 `YuNetFaceLocator` | [YuNet, opencv_zoo](https://github.com/opencv/opencv_zoo) |
| **Alpha "over".** `out = α·fg + (1−α)·bg`; JPEG has no alpha ⇒ flatten to white | `pillow_renderer.flatten` | [Porter & Duff 1984](https://dl.acm.org/doi/10.1145/800031.808606) |
| **EXIF orientation is a lie about pixels.** Rotate pixels, drop the tag | `pillow_renderer.load` + EXIF test | [EXIF orientation explained](https://jdhao.github.io/2019/07/31/image_rotation_exif_info/) |
| **DPI: metadata vs. truth.** Standalone image: embed it (printers obey). Inside PDF: ignore it, derive from page geometry (`EffectiveDpi`) | photo rule #3 · pdf rule #3 | `DOMAIN.md` |
| **PDF pages are programs; the CTM is machine state.** True image size on page = interpret the content stream (`q/Q` push/pop, `cm` matrix concat), take `hypot(a,b)` per `Do` — a mediabox shortcut breaks the moment a page has 2 images or a Form XObject | W5 CTM census (ported from ocrmypdf `_contentstream.py`) | [PDF 32000 §8.3](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf) |

## Algorithms

| Mental model | Used at | Deep dive |
|---|---|---|
| **Binary-search the answer** over a monotone, expensive predicate (encode-and-measure) | `TargetSizeSearch` · `_encode_under_ceiling` | [CP-algorithms: binary search on answer](https://cp-algorithms.com/num_methods/binary_search.html) |
| **Proportional (pro-rata) allocation.** Byte budget ∝ rendered area = spend bytes where eyes go | `BudgetDecomposition.allocate` | — |
| **Integer grid + slack→gutters.** `⌊usable/cell⌋` capacity; n+1 equal gaps center the grid; integer px only (no FP drift) | `SheetLayoutService` | — |
| **Content-addressed identity.** SHA-256 = file identity (same idea as git objects) | `MediaFile.content_hash` | [Git internals: objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects) |

## OS / systems

| Mental model | Used at | Deep dive |
|---|---|---|
| **Three ways to call code:** in-process C ext (fast, shared fate) · subprocess exec (isolated, AGPL quarantine) · long-lived child on stdio pipes (MCP) | pikepdf / ghostscript adapter / `mcp_server` | [APUE ch. 8, 15](https://www.apuebook.com/) |
| **stdio JSON-RPC.** Pipes = oldest IPC; process boundary = security boundary; no ports, no auth surface | `.mcp.json` → `server.py` | [MCP spec](https://modelcontextprotocol.io/) |
| **Tempdir per request + cleanup *after* response streams** (BackgroundTask ordering) | `api/app.py:_workdir` | [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) |
| **venv = userspace isolation; stamp file = make-style "inputs changed?"** idempotent bootstrap; activation must happen in the launching shell (env is per-process, inherited) | `tools/venv.sh` + zshrc hook | [Python venv docs](https://docs.python.org/3/library/venv.html) |
| **One script, three entrypoints** via shebang + symlink: shell, `sh_binary`, git hook | `tools/pre-commit.sh` | — |
| **Hermetic builds.** Declared inputs ⇒ reproducible outputs; zero-directive Gazelle = convention over configuration | `BAZEL_MIGRATION.md` | [Bazel hermeticity](https://bazel.build/basics/hermeticity) |
| **Reject before decode.** Resource limits belong *before* the expensive operation (check declared pixels/pages/bytes, then parse) — and defaults must be ON: the two biggest OSS doc-servers ship limits disabled and users forget | W3 caps (imgproxy `MAX_SRC_RESOLUTION` pattern) | [imgproxy config](https://docs.imgproxy.net/latest/configuration/options) |
| **Process recycling beats leak-hunting.** Long-lived native-lib workers (Pillow/pikepdf ≙ Chromium in gotenberg) get restarted every N tasks (`max_tasks_per_child`) — fragmentation/leak defense as policy, not debugging | pre-hosting set (HLD runtime) | [gotenberg config](https://gotenberg.dev/docs/configuration) |

## Architecture

| Mental model | Used at | Deep dive |
|---|---|---|
| **Hexagonal: arrows point inward.** domain→application→ports→infra; swap adapters, test math with zero I/O | every context | [Cockburn, Hexagonal architecture](https://alistair.cockburn.us/hexagonal-architecture/) |
| **ABC = nominal ("I declare I implement"); Protocol = structural ("I happen to fit")** — Protocol when infra must not import application | `PhotoRenderer` vs `StructuralOptimizer` | [PEP 544](https://peps.python.org/pep-0544/) |
| **Generic port, no `Any`.** `PhotoRenderer[ImageT]`; adapter binds `PIL.Image` | `photo_context/ports.py` | [mypy generics](https://mypy.readthedocs.io/en/stable/generics.html) |
| **Frozen dataclass = invalid states unrepresentable** (validate once in `__post_init__`) | all value objects | [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) |
| **Invariants are tests, not comments** ("never larger", "lossless = bit-identical") | `*_test.py` hard-rule tests | — |

## Reading order
JPEG paper → SSIM paper → Porter-Duff → APUE pipes → Cockburn hexagonal. Each maps
directly onto one module you can read immediately after.
