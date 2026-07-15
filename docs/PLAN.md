# PLAN — Implementation plan & status

> Doc stack: [PRD](PRD.md) → [HLD](HLD.md) → [LLD](LLD.md) → **PLAN (this)** → code.
> Inputs: [REVIEW](REVIEW.md) (adaptive review, 2026-07-15) · [RESEARCH](RESEARCH.md) (OSS/SOTA study, 2026-07-15).
> Update the checkbox + date when a phase lands; scope shifts fix PRD/HLD/LLD first.

**Status legend:** ✅ done · 🔄 in progress · ⬜ pending · ⏸ blocked

---

## Done (Phases 0–6, 2026-07-14/15)

- ✅ Foundation: DDD skeleton, shared kernel, pdf/image contexts, target-size engine (pikepdf ⭐), engine benchmark (`ANALYSIS.md`), Bazel polyglot build validated (8.6.0, `build //...` + `test` green)
- ✅ Doc stack (PRD/HLD/LLD/PLAN + DOMAIN photo context) · dev infra (venv.sh, cli.sh launcher, pre-commit gate, locks ×2 platforms, `//:venv //:gazelle //:pre-commit`, hclaude hook)
- ✅ photo_context (presets, sheet math, HEIC, byte ceiling) · lossless (mozjpeg/Pillow/pikepdf) · CLI/MCP/API/skills · 26 tests + 6/6 bazel targets
- ✅ Adaptive review → `REVIEW.md` (1 P0 · 40 P1 · 56 P2 · 35 P3) · Deep research → `RESEARCH.md` (verdict: design unrepresented in OSS; SSIM floor invalidated; adoption backlog)

---

## Improvement program (waves; REVIEW themes × RESEARCH adoptions)

Every wave ships with its tests in the same change (implementer skill rule). Testing
workstream items marked **T**.

### Wave 1 — Honesty & licensing (S) ✅ 2026-07-15
- ✅ **P0**: `PikepdfInspector` (license-clean) serves MCP + new HTTP `/inspect`; PyMuPDF → CLI-only
- ✅ **T** N2 contract test (`contracts_test.py`): fresh-subprocess import check + source grep; passes under pytest AND bazel
- ✅ Parity truth: `strip_metadata` on MCP+HTTP; escalation divergence documented as deliberate (CLAUDE.md, MCP description)
- ✅ Floor-violation fallback fixed: `_lowest_floor_quality` — floor is the invariant, never `quality_range[0]`
- ✅ **T** regression tests (`recompress_test.py`, fake codec/meter)

### Wave 2 — Boundaries & one-home (M) ✅ 2026-07-15 (one carry-over)
- ✅ Kernel moves: `ImageKind`, `ResampleFilter`, `CompressionTarget`, `TargetSizeSearch`, `LosslessOutcome` + constants → `shared_kernel`; image↔pdf coupling ended
- ✅ Photo `_encode_under_ceiling` reuses `TargetSizeSearch` (memoized — winner never re-encoded)
- ✅ Constants: `DEFAULT_TARGET_KB`, `WHITE`, `GUIDE_COLOR`, `PDF_POINTS_PER_INCH`; api/mcp use kernel defaults; CLI `choices=sorted(PRESETS/SHEETS)`, one `build_engines()` registry
- ✅ `MergePdfs` use case + `PdfMerger` port + `PikepdfMerger`; CLI+MCP call it; `PhotoSpec.describe()`
- ✅ Dead layer deleted: `PageRange`, `SplitSpec`, `Splitter`, `PdfCodec`+`PyMuPdfCodec`, 3 domain events, `content_hash`; DOMAIN.md reconciled
- ✅ **T** gazelle re-run; pytest 29 (+1 slow) + bazel 8/8 green
- ⬜ carry-over → W5: template-method extraction of twin compressor bodies (deferred — touches the same code as the W5 census rewrite; do together)

### Wave 3 — Serving hardening (M) ⬜ (prior art: RESEARCH §4)
- ⬜ Upload cap: middleware `Content-Length` + counted chunk copy → 413 (`MAX_UPLOAD_BYTES`, gotenberg pattern — *enabled* by default)
- ⬜ Reject-before-decode: explicit `Image.MAX_IMAGE_PIXELS` (imgproxy 50 Mpx pattern), PDF page/image caps → 422; catch `DecompressionBombError`/`pikepdf.PdfError` → 413/422; logged 500 handler
- ⬜ MCP path confinement: `DOC_TOOLKIT_ALLOWED_DIRS` checked in `_resolve` **and on outputs**; `list_allowed_dirs` tool (MCP filesystem-server norm); no-clobber unless `overwrite=True`
- ⬜ Per-op timeout (30 s default, per-endpoint dict — Stirling pattern); gs subprocess `timeout=` + stderr in errors
- ⬜ stdlib `logging` throughout (stderr on MCP stdio); correlation-id middleware; narrow `suppress(Exception)` → `pikepdf.PdfError` + warn
- ⬜ Typed error set (`InvalidInput`, `UnreadableDocument`) in shared_kernel; deliberate mapping per surface (CLI exit 2 + top-level handler, HTTP 4xx/5xx, MCP isError)
- ⬜ **T** tests: 413 oversize, 422 corrupt/bomb, allowlist rejection, no-clobber, timeout path

### Wave 4 — Testing completion (M) 🔄 (REVIEW axis 5–7)
- ✅ **T** `conftest.py` created (fixtures: `portrait`, `jpeg_bytes`, `scan_pdf`, `api_client`); ⬜ migrate the 5 existing test files onto them
- ✅ **T** pytest markers `slow`/`perf`/`manual` + default `addopts` exclusion; OCI 2000² test tagged `slow`
- ⬜ **T** missing suites: `TargetSizeSearch`/`BudgetDecomposition` (pure), compressor short-circuit/rollback/escalation (stub engine), CLI e2e (argv), MCP tools (direct calls), `NumpySsimMeter`, hard-rule-#2 named test, `PageRange` boundaries
- ⬜ **T** perf tier: `@pytest.mark.perf` budget assertions (photo < 1 s; 16-page corpus PDF < 30 s; API round-trip < 5 s) on reference inputs; **stress**: 50-page synthetic scan, 50 Mpx-adjacent image, concurrent API calls — `manual` mark
- ⬜ **T** `pytest-cov` in pre-commit (not default addopts); coverage floor 80% on domain+application layers
- ⬜ **T** golden files: commit reference outputs (photo, sheet, compressed pdf) + byte/SSIM-tolerance compare — catches Pillow/mozjpeg version drift

### Wave 5 — Domain truth & census correctness (L) ⬜ (RESEARCH §1)
- ⬜ CTM-true DPI census: port ocrmypdf `_contentstream.py` interpreter (MPL-2.0, ~130 lines) — per-placement DPI via `hypot`, Form-XObject recursion, fixes hard rule #3 and budget ∝ *actual* rendered area
- ⬜ Census safety rails: skip SMask-bearing/mask/JPX/CCITT-G3/`/Decode`-array/<8 px images; multi-filter guard; census `Codec` from `/Filter` (stop hardcoding JPEG)
- ⬜ Colorspace discipline: preserve DeviceGray (gray JPEG ~3× smaller); `keep_fields` whitelist on XObject rewrite; never touch CMYK/ICC contone
- ⬜ Hard rule #2: fix direction (gray-Lanczos + Otsu → CCITT G4; NEAREST comment corrected); optional JBIG2 branch behind port (jbig2enc, 2–5× over G4)
- ⬜ Hard rule #4: single floor-enforcement point (accept/escalate/warn); gs adapter scores its output via `QualityMeter`
- ⬜ DOMAIN.md reconciliation: delete/mark-planned fictional names; document mediabox→CTM change; add scale envelope (max pages/px/MB)
- ⬜ **T** wild-PDF corpus tests: SMask, gray, CMYK, multi-image page, form-XObject fixtures (synthesized via pikepdf) — census + compress must not corrupt

### Wave 6 — Metrics & encoder frontier (M/L) ⬜ (RESEARCH §3)
- ⬜ `Ssimulacra2Meter` adapter (subprocess `ssimulacra2_rs` or vendored py impl behind `QualityMeter`); floor 70 portal / 80 archival; compare codec-loss only (resized-vs-candidate), native resolution; SSIM meter stays as fast fallback
- ⬜ `JpegliCodec` adapter: subprocess `cjpegli --target_size` behind `ImageCodec`; binary search demotes to fallback path; benchmark vs Pillow on corpus (extend `ANALYSIS.md`)
- ⬜ Hot-loop economies: cache reference luma per call; search returns winning bytes (kill re-encode); lazy scoring (size check first); probes without `optimize`
- ⬜ Lossless upgrades: `pyoxipng` for PNG; `deflate_jpegs` + `remove_unreferenced_resources()` in structural pass; image dedup-by-hash before budget allocation (Stirling pattern)
- ⬜ **T** perf benchmarks before/after each economy (assert ≥30% encode-count reduction); metric A/B on corpus logged to `ANALYSIS.md`

### Wave 7 — Photo intelligence (Phase 8 concretized) ⬜ (RESEARCH §2)
- ⬜ `FaceLocator` CV adapter: YuNet via `cv2.FaceDetectorYN` (345 KB, Apache-2.0) — anchor from face center, roll correction from eye landmarks; exactly-one-face validation → warning
- ⬜ **F8** `BackgroundMatter` port + MODNet ONNX adapter (24.7 MB, Apache-2.0, CPU <1 s; onnxruntime); compose with existing `flatten()`; **never RMBG-1.4 (non-commercial)**
- ⬜ PhotoSpec enrichment: `min_bytes` (+NUL padding — portals enforce minimums), `head_height_frac`/`eye_height_frac` compliance rules as data (idify schema shape); verify + warn channel
- ⬜ Sheet transpose check (keep orientation with more photos — matters for 35×45 mm specs)
- ⬜ **F9** NL-directed cleanup: separate mini doc-stack `docs/v2/` first (SAM-style grounding + LaMa inpainting, strict-local default) — unchanged from PRD
- ⬜ **T** compliance fixtures: synthetic faces at known head heights; matting golden masks; landmark determinism

### Later (unchanged)
- ⬜ CI (GitHub Actions: `tools/pre-commit.sh` + `bazel test //...`) — becomes urgent at Wave 3
- ✅ 2026-07-15: `tools/venv.sh` rewritten on **uv** — `uv venv --python 3.13` + `uv pip sync <platform lock>` (exact sync, installs from the SAME lock Bazel consumes; fixes REVIEW build P1 + the 3.12/3.13 toolchain skew); `tools/lock.sh` = documented lock regen; mypy → 3.13
- ⬜ Go/Rust ports of photo_context; NL tool layer; hosted Web UI (+ process pool with recycling, bounded concurrency/429, bearer token — RESEARCH §4 pre-hosting set)
- ⬜ **Containerize (decided 2026-07-15: deferred)** — trigger = hosted-UI deploy OR second-machine distribution, not before (macOS VM friction; drift is covered by locks+golden files). Then: `rules_oci` (`oci_image`/`oci_load`/`oci_push`) on `py_binary`, linux platform transition; prerequisite = linux-aarch64 lock + native-wheel check
- ⬜ MCP/HTTP lifecycle note: stdio MCP spawns on demand (no boot/wake concern); only an always-on HTTP API would need launchd — none planned

### Wave 8 — use-case candidates (PRD triage before any code)
Ranked by fit; the corpus itself motivates the first two (`thumbprint.jpg`, hand-built `oci_split_compressed/`):
- ⬜ Signature/thumbprint `PhotoSpec` presets (OCI requirements — two data rows)
- ⬜ **Packet builder**: named checklist → merged, bookmarked, per-portal size-capped PDF (census+merge+compress already exist)
- ⬜ `SplitPdf` + page ops (extract/reorder/rotate/delete) — already promised in DOMAIN.md
- ⬜ Scan cleanup: deskew + perspective correction (photo-of-document → flat scan)
- ⬜ OCR → searchable PDF (ocrmypdf is MPL-2.0 — license-clean adapter)
- ⬜ Image ⇄ PDF conversion · HEIC batch · metadata scrub · purpose watermark
- ⬜ Photo compliance checker (score existing photo vs spec — falls out of W7 landmarks)
