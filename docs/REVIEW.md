# REVIEW — adaptive multi-axis, 2026-07-15

> Produced by `/adaptive-review`: 6 parallel single-axis subagents over 11 axes.
> Tools ran first (ruff/mypy/pytest/bazel all green — excluded from findings).

## Scorecard

| Axis | Verdict | P0 | P1 | P2 | P3 |
|---|---|--:|--:|--:|--:|
| style | boundary typing decays to implicit-Any where mypy can't see | – | 3 | 4 | 5 |
| smells | dead speculative layer + twin compressors + constants sprawl | – | 4 | 8 | 3 |
| architecture | contexts mutually coupled; 2 hard rules contradicted by code citing them | – | 6 | 6 | 2 |
| principles | DRY/OCP/YAGNI eroding at edges; core algorithm well-homed | – | 4 | 6 | 4 |
| testing | what's tested is tested well; pyramid missing top + a wing | – | 6 | 5 | 4 |
| performance | right algorithms, ~2× avoidable hot-loop cost; not hosting-ready | – | 4 | 6 | 5 |
| security | **AGPL quarantine breached on a served path**; N1 privacy verified clean | 1 | 4 | 3 | 2 |
| errors | zero logging; two-exception net turns corrupt PDFs into blind 500s | – | 4 | 5 | 4 |
| api | CLI is the only full surface; MCP/HTTP quietly narrower | – | 3 | 6 | 1 |
| build | above-average hygiene; bootstrap bypasses its own locks | – | 1 | 3 | 3 |
| docs | unusually current; 3 promises drifted (`/inspect`, exit 2, "same results") | – | 1 | 4 | 2 |
| **Σ** | | **1** | **40** | **56** | **35** |

## Cross-axis themes (root causes)

1. **Surface-parity fiction** — CLI is the real product; MCP/HTTP/docs claim parity they don't deliver: MCP `inspect_pdf` imports AGPL (the P0), MCP/HTTP compress lack gs escalation + `strip_metadata`, HTTP lacks `/inspect` + sheet, CLAUDE.md says "same results". Nothing *tests* N2.
2. **image↔pdf contexts are one context in denial** — bidirectional imports; `ImageKind`, `ResampleFilter`, `CompressionTarget`, `TargetSizeSearch`, `LosslessOutcome` belong in `shared_kernel`; the wrong-direction dep is masked by dropped return annotations.
3. **Two homes for one fact** — twin compressor bodies (~80% identical); quality binary-search reimplemented in photo (docstring claims reuse it doesn't do); compress defaults restated 4×; white/#bbb/72ppi/KB-conversion sprawl; merge + spec-serialization + engine registry duplicated per surface.
4. **Documentation fiction & dead layer** — DOMAIN.md names with no code (`PdfDocument`, `SplitPdf`, `CompressImageToTarget`…); ~150 LoC dead (`PageRange`, `SplitSpec`, `Splitter`, `PdfCodec`+adapter, 3 domain events, `content_hash`, `DSSIM`/`BUTTERAUGLI`); **hard rule #2 encoded backwards** (NEAREST-for-bitonal vs mandated gray-Lanczos+Otsu); **hard rule #4 enforced nowhere** (below-floor results returnable; gs ignores floor); `EffectiveDpi` from mediabox, not per-image CTM → budget ∝ page area.
5. **Blind in the field** — zero logging anywhere; gs subprocess has no timeout; `suppress(Exception)` skews budget math silently; CLI has no top-level handler (tracebacks, exit 1 not the documented 2).
6. **Unbounded served inputs** — no upload size cap, no page/image-count cap, Pillow bomb limit implicit and its error escapes handlers as 500.
7. **Hot loop pays ~2×** — reference luma recomputed per probe; winning encode discarded and redone; SSIM computed for oversized candidates; probes encode with `optimize=True`.
8. **Test pyramid gaps** — lossy pipeline/escalation, both domain services, CLI, MCP: zero coverage; no `conftest.py` (helpers copy-pasted 4×); no markers → slow test in default run; no perf tier; no coverage tooling.
9. **Reproducibility leak** — `tools/venv.sh` installs unpinned from `.in`, bypassing the platform locks Bazel uses; no `tools/lock.sh`; no CI enforcing the gate.

## P0 — fix before anything else

| # | file:line | Finding | Fix |
|---|---|---|---|
| 1 | `mcp_server/server.py:153` | Served MCP tool `inspect_pdf` imports AGPL `PyMuPdfInspector` — N2 violation | License-clean inspector (pikepdf/pypdfium2, both already deps); PyMuPDF stays CLI-only; add an import-contract test so it can't recur |

## P1 — should fix (deduped, by theme)

| Theme | Items |
|---|---|
| Parity (1) | HTTP `/inspect` missing vs LLD:70 · MCP/HTTP compress lacks escalation while CLI has it (CLAUDE.md "same results" false) · N2 untested — add import-linter/pytest contract |
| Boundaries (2) | Move `ImageKind`/`ResampleFilter`/`CompressionTarget`/`TargetSizeSearch`/`LosslessOutcome` → `shared_kernel`; annotate `StructuralOptimizer.optimize`/`CompressPdfLossless.__call__`; make `ImageCodec` generic (`ImageT`) |
| One-home (3) | Photo `_encode_under_ceiling` → reuse `TargetSizeSearch` · extract shared compressor orchestrator (template method) · single `DEFAULT_TARGET_KB`/`dpi_cap`/`floor` home · CLI `choices=sorted(PRESETS)` etc. (OCP) |
| Domain truth (4) | Delete dead layer (or implement `SplitPdf`) · fix/park hard rule #2 branch · enforce hard rule #4 at one point (floor check + escalate/warn) · reconcile DOMAIN.md names · per-image CTM for `EffectiveDpi` (or document the approximation) |
| Ops (5,6) | `logging` throughout (escalations, suppressed errors, 500s) · gs `timeout=` + stderr in errors · narrow `suppress(Exception)` → `pikepdf.PdfError` + warn · API: size cap (413), `PdfError`/bomb → 422/413, logged 500 handler · MCP: no silent overwrite of existing `out_path` |
| Perf (7) | Cache reference luma per `recompress_to_slice` · return winning bytes from search (kill re-encode) · perf-marked budget test + scale envelope in DOMAIN.md |
| Tests (8) | `conftest.py` with shared fixtures · markers `slow/perf/manual` + addopts exclusion · tests: `TargetSizeSearch`/`BudgetDecomposition`, compressor short-circuit/rollback/escalation (stub engine), CLI e2e, MCP tools |
| Build (9) | `tools/venv.sh` installs from platform lock; `tools/lock.sh`; CI running `tools/pre-commit.sh` + `bazel test` |

## P2/P3 — worth batching (pointers)

Constants module sweep (`WHITE`, `GUIDE_COLOR`, `PDF_POINTS_PER_INCH`, q=95, KB helper) · census `Codec` from `/Filter` not hardcoded JPEG · `MergePdfs` use case · `PhotoSpec.describe()` shared serializer · lazy SSIM (skip oversized) · probe encodes without `optimize` · `MediaFile` identity claim vs `__eq__` (or delete `content_hash`) · `CenterFaceLocator` → infrastructure · CLI: top-level handler exit 2, `--help` strings, `specs` subcommand · benchmark → own module · engine name canonicalization (`gs` vs `ghostscript`) · shared_kernel out of `__init__.py` · `.gitignore` cache dirs · mypy 3.13 · sanitize `file.filename` in headers · runtime-only lock for `pip.parse` · explicit `Image.MAX_IMAGE_PIXELS` · `TestClient` as fixture · unconditional hard-rule-1 assert · pytest-cov in gate.

## Fix waves (proposed order)

| Wave | Scope | Size |
|---|---|---|
| 1 | P0 + N2 contract test + parity truth (docs or code, per item) | S |
| 2 | Boundary moves to shared_kernel + one-home consolidation (mechanical, gazelle re-run) | M |
| 3 | Ops hardening: logging, timeouts, error taxonomy + mapping, API limits | M |
| 4 | Tests: conftest, markers, missing suites, perf tier, coverage in gate | M |
| 5 | Domain truth: hard rules #2/#4, CTM DPI, DOMAIN.md reconciliation, dead-layer decision | L |
| 6 | Perf: luma cache, search returns bytes, lazy SSIM · build: lock-based venv, lock.sh, CI | M |

**Overall verdict:** architecture intent is real and the algorithms are right, but the repo has one licensing P0 on a served path, two hard rules its own docs swear by that the code contradicts, and a CLI-only feature set that every other surface (and doc) overstates. Waves 1–3 make it honest; 4–6 make it durable.
