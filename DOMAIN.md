# PDF & Image Toolkit — Ubiquitous Language

> This document is the **shared contract**. Python, Rust, and Go each mirror these
> exact names and boundaries so a feature always has the same home in every language.
> When you add a concept, add it *here first*, then in each language.

Adopted from the fable DDD strategy. Compression is **target-size driven**: hit a
byte budget with the maximum perceptual quality that clears a quality floor.

---

## Bounded Contexts

| Context | Responsibility | Package (Py) | Module (Rust) | Package (Go) |
|---|---|---|---|---|
| **pdf** | Splitting, PDF-level compression, page/image census | `pdf_context` | `pdf_context` | `pdfcontext` |
| **image** | Standalone image compression (incl. lossless), format conversion, quality metrics | `image_context` | `image_context` | `imagecontext` |
| **photo** | Passport-style photo production (compliance presets), print-sheet composition | `photo_context` | `photo_context` | `photocontext` |
| **nl** *(later)* | Natural-language → Command (tool schemas), agent loop | `nl_context` | `nl_context` | `nlcontext` |

Each context has the same 4 layers: `domain/` → `application/` (use cases) →
`ports` (interfaces) → `infrastructure/` (adapters). **Domain never imports a library.**

---

## Shared Kernel (`shared_kernel`)

Value objects used by all contexts. Immutable; validated on construction.
**Moved here 2026-07-15 (W2):** `ImageKind`, `ResampleFilter`, `CompressionTarget`,
`TargetSizeSearch` (one home for the quality search), `LosslessOutcome`, and constants
(`WHITE`, `GUIDE_COLOR`, `PDF_POINTS_PER_INCH`, `DEFAULT_TARGET_KB`) — ends the
image↔pdf bidirectional coupling flagged in docs/REVIEW.md.

| Type | Fields | Invariant / Behavior |
|---|---|---|
| `MediaFile` | `path`, `size_bytes` | Value object keyed by path. `size_kb`, `exists`. |
| `ByteBudget` | `target_bytes`, `tolerance` (e.g. `-0%,+5%`) | `ceiling()`, `contains(n)`, `overshoot(n)`. |
| `QualityFloor` | `metric` (SSIM\|DSSIM\|Butteraugli\|**SSIMULACRA2** planned W6), `threshold` | `accepts(score) -> bool`. A **domain invariant** — an adapter may not return a result below it. ⚠ 2026-07-15: SSIM 0.90 shown decorative (docs/RESEARCH.md §3); target = SSIMULACRA2 ≥ 70/80. Enforcement point lands in W5 (docs/PLAN.md). |
| `PerceptualScore` | `metric`, `value` | Comparable within a metric. |
| `EffectiveDpi` | `pixels`, `rendered_inches` | Computed from page **geometry (CTM)**, *never* image metadata. `value = pixels / rendered_inches`. |

---

## `pdf` Context

### Domain
| Type | Kind | Notes |
|---|---|---|
| `PdfDocument` | Aggregate root *(planned)* | Not yet in code; census operates on `MediaFile`. |
| `PageRange` / `SplitSpec` | *(deleted 2026-07-15, W2 — YAGNI)* | Restore from git when `SplitPdf` is actually built. |
| `EmbeddedImage` | Entity | `xref`, `width`, `height`, `ImageKind`, `Codec`, `EffectiveDpi`, `rendered_area`. |
| `ImageKind` | Enum | `Bitonal` \| `Grayscale` \| `Color` — drives resample + re-encode strategy. |
| `Codec` | Enum | `Jpeg`(DCTDecode) \| `CcittG4`(CCITTFaxDecode) \| `Flate` \| `Png` \| `Jbig2` \| `Raw`. |
| `ResampleFilter` | Enum | `Nearest` (bitonal only) \| `Lanczos` (contone). |
| `CompressionTarget` | Value object | `ByteBudget` + `QualityFloor` + optional `dpi_cap` + `dpi_range`. |
| `CompressionRecipe` | Value object | Per-image decision: `dpi`, `quality`, `Codec`, `ResampleFilter`. |
| `CompressionResult` | Value object | output `MediaFile`, `before/after_bytes`, `dpi_used`, `quality_used`, `PerceptualScore`, `engine`, `elapsed_ms`. |
| `DocumentCensus` | Value object | image inventory, non-image bytes, per-image `EffectiveDpi` (output of inspect). |

### Domain events *(deleted 2026-07-15, W2)*
Escalation is recorded in `CompressionResult.escalated`; typed events return
when the retry loop (algorithm step 6) is implemented — see docs/PLAN.md W5.

### Ports (interfaces / traits)
| Port | Method(s) |
|---|---|
| `PdfInspector` | `inspect(doc) -> DocumentCensus` — adapters: `PikepdfInspector` (license-clean, served) · `PyMuPdfInspector` (AGPL, CLI-only) |
| `Compressor` | `compress(doc, CompressionTarget, out) -> CompressionResult` |
| `PdfMerger` | `merge([MediaFile], out) -> (MediaFile, pages)` |
| `StructuralOptimizer` | `optimize(doc, out, strip_metadata) -> LosslessOutcome` |
| *(`Splitter`/`PdfCodec` deleted 2026-07-15, W2 — unused; git remembers)* | |

### Domain services (pure orchestration, no library imports)
- **`TargetSizeSearch`** — binary search over encoder quality (§ quality search),
  then over dimensions if quality floor conflicts with budget. Enforces `QualityFloor`.
- **`BudgetDecomposition`** — allocate a PDF's byte budget across images ∝ rendered area;
  reserve non-image bytes measured after the structural pass.

### Application use cases (= NL tool schemas later)
`InspectDocument` · `SplitPdf` · `CompressPdfToTarget`

---

## `image` Context

### Domain
| Type | Notes |
|---|---|
| `ImageAsset` | Aggregate root; identity = content hash. |
| `ImageFormat` | `Jpeg` \| `Png` \| `WebP` \| `Avif`. |
| `FormatDecision` | photo→JPEG/AVIF · <256 colors→PNG8(quantize) · transparency+photo→WebP/AVIF. |
| `CompressionTarget`, `CompressionResult` | Reuse shared-kernel `ByteBudget`/`QualityFloor`. |

### Ports
| Port | Method(s) |
|---|---|
| `ImageCodec` | `decode(bytes)` · `resize(img, w, h, ResampleFilter)` · `encode(img, format, quality) -> bytes` |
| `QualityMeter` | `score(original, candidate) -> PerceptualScore` |

### Application use cases
`CompressImageToTarget` · `ConvertImage` · `Batch` · `CompressImageLossless`

### Lossless (added 2026-07-14)
| Type | Notes |
|---|---|
| `LosslessOptimizer` (port) | `optimize(bytes, fmt) -> bytes` — **pixels must be bit-exact**. JPEG = entropy-coding-only (mozjpeg); PNG = recompress. |
| `LosslessOutcome` | output `MediaFile`, `before/after_bytes`, `changed`. Hard rule #1 applies. |

---

## `photo` Context

Passport-style photo production + print-sheet composition. See `docs/LLD.md` §2–4
for full signatures. Compliance specs are **data presets**, never code branches.

### Domain
| Type | Notes |
|---|---|
| `PhotoSpec` | Value object preset: exact `width_px×height_px`, `dpi`, `background`, optional `max_bytes` (portal ceiling), human `notes`. Presets: `us_passport`, `india_passport`, `india_oci` (≤ 200 KB). |
| `SheetSpec` | Print sheet: `width_in×height_in` @ `dpi` (300). `4x6` → 1200×1800 px. |
| `SheetLayout` | Computed tiling: `cols×rows`, cell px, offsets. 2×2″ on 4×6″ → 6-up. |

### Domain services
- **`SheetLayoutService`** — pure tiling math; leftover space becomes uniform gutters (cut lanes).

### Ports
| Port | Method(s) |
|---|---|
| `PhotoRenderer` | `load` (HEIC/JPG/PNG, EXIF-transposed) · `crop_to_aspect` · `resize` · `flatten` · `encode_jpeg(quality, dpi)` · `compose(sheet)` |
| `FaceLocator` | `anchor(w, h) -> (fx, fy)` crop center. v1: `CenterFaceLocator` (0.5, 0.45); CV adapter later. |

### Application use cases
`CreatePassportPhoto` (byte ceiling via the shared quality binary search) · `ComposePrintSheet`

### Photo hard rules
1. Byte-ceiling enforcement reuses the § quality search — one algorithm home.
2. Never silently upscale: flag `upscaled=True` + warning when source < spec pixels.
3. Output DPI metadata always embedded (print sizing depends on it).

---

## Target-Size Algorithm (shared across languages)

```
compress_to_target(doc, target):
  1. structural pass (lossless): gc, dedupe images, object streams, strip metadata
  2. census: EffectiveDpi per image from geometry (NOT metadata)
  3. budget = target.bytes − non_image_bytes_after_structural
  4. per image, allocate budget ∝ rendered_area
  5. per image, by ImageKind:
       Bitonal   -> grayscale downsample + Lanczos + re-threshold(Otsu) -> CCITT G4  (never NN, never JPEG)
       contone   -> cap EffectiveDpi (150 screen / 225 print),
                    binary-search encoder quality to fit slice, enforce QualityFloor
  6. reassemble; if over budget -> lower global dpi_cap 25%, retry (≤3 outer loops)
  7. escalate to Ghostscript adapter only on BudgetMissed
```

Quality binary search (monotonic size↔quality):
```
lo, hi = Q_MIN, Q_MAX
best = None
while hi - lo > 1:
  q = (lo+hi)//2; buf = encode(img, q)
  if len(buf) <= slice_bytes: best = (q, buf); lo = q     # largest q that fits
  else: hi = q
return best
```

---

## Hard Rules (encode as tests in every language)

1. **Never emit output larger than input** — return the original instead.
2. **Bitonal scans**: grayscale-downsample → re-threshold → CCITT G4. Never nearest-neighbor
   resize into gray, never JPEG (explodes size 5–10×).
3. **Effective DPI from geometry (CTM)**, never from image metadata (scanners often omit/lie).
4. **Quality floor is a domain invariant** — an adapter may not return a result below it.
5. **Every adapter behind a port**; AGPL deps (PyMuPDF, MuPDF, Ghostscript) isolated to
   their adapter module so they're swappable if the code is ever distributed.
6. **Type discipline (Python reference):** value objects & results = `@dataclass(frozen=True)`;
   use cases = `@dataclass`; ports = `ABC` when adapters subclass deliberately,
   `typing.Protocol` when satisfaction should be structural (no inward import).
   Go mirrors ports as interfaces, Rust as traits — same names, same methods.

---

## Engines (Python reference — measured 2026-07-14)

The `Compressor` port has three interchangeable adapters. Default is the **license-clean
composite**; Ghostscript is quarantined to escalation. See `docs/ANALYSIS.md`.

| Engine (`Compressor.name`) | Stack | License | Role |
|---|---|---|---|
| **`pikepdf`** ⭐ default | pikepdf (surgery+structural) + Pillow (recompress) + pypdfium2 (render/SSIM) | MPL-2.0 / HPND / BSD-Apache — **no AGPL** | Primary. Surgically rewrites image XObjects; highest fidelity. |
| `pymupdf+pillow` | PyMuPDF + Pillow | **AGPL** | Alternative; smallest files. Avoid for network-served use (§13). |
| `ghostscript` | `gs` subprocess | AGPL | **Escalation only**, fires on `BudgetMissed`. |

> **Why pikepdf is default:** the hosted-UI roadmap makes AGPL §13 network copyleft a real
> obligation. pikepdf + pypdfium2 + Pillow serve over a network with no source-disclosure
> requirement, and measured *higher* SSIM than both AGPL engines. `pypdfium2` is a
> **renderer** (rasterize/SSIM role) — the surgical image-stream replacement is pikepdf's job.

---

## This corpus (measured 2026-07-14)

The `oci_*` scans are **not** bitonal: every page is a single **RGB JPEG (DCTDecode),
8 bpc, 6600×5100 px ≈ 776 DPI** on a Letter page. So the *contone* branch applies —
LANCZOS downsample + JPEG re-encode. The bitonal branch is implemented for reuse but
does not trigger here.
