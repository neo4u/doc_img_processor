# Graph Report - /Users/prasanthk/doc_img_processor  (2026-07-15)

## Corpus Check
- Corpus is ~28,972 words - fits in a single context window. You may not need a graph.

## Summary
- 787 nodes · 1498 edges · 56 communities (44 shown, 12 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.62)
- Token cost: 108,860 input · 0 output

## Community Hubs (Navigation)
- Image Codec & SSIM Adapters
- Image Compression Use Cases
- Skills & Serving Docs
- Python CLI
- Go CLI & Ghostscript
- Rust Image Infra
- Rust PDF Domain
- Go Shared Kernel
- MCP Server Tools
- Photo Application Tests
- Rust CLI & Kernel
- FastAPI Endpoints
- PDF Lossless Optimizer
- Rust lopdf Adapters
- PhotoRenderer Port
- Pikepdf Compressor
- Go Domain Services
- Rust Ghostscript Adapter
- Go pdfcpu Adapter
- Sheet Layout Service
- PDF Use-Case Callables
- CreatePassportPhoto Use Case
- Shared Test Fixtures
- Photo Application Layer
- Go Image Codec
- API Round-Trip Tests
- PDF Ports
- Photo Domain
- Sheet Spec Validation
- Numpy SSIM Internals
- Fragment: ports.go
- Fragment: .__call__()
- Fragment: domain.go
- Fragment: .mcp.json
- Fragment: .anchor()
- Fragment: ports.rs
- Fragment: domain.rs
- Fragment: cli.sh
- Fragment: install-hooks.sh
- Fragment: lock.sh
- Fragment: mcp.sh
- Fragment: mcp-bazel.sh
- Fragment: pre-commit.sh
- Fragment: venv.sh
- Fragment: pdftoolkit

## God Nodes (most connected - your core abstractions)
1. `DocumentCensus` - 24 edges
2. `PikepdfCompressor` - 22 edges
3. `CompressionResult` - 20 edges
4. `ImageCodec` - 18 edges
5. `MediaFile` - 18 edges
6. `recompress_to_slice()` - 17 edges
7. `QualityMeter` - 16 edges
8. `NativeImageCompressor` - 16 edges
9. `PillowPhotoRenderer` - 16 edges
10. `EffectiveDpi` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Doc Toolkit Router Skill (duplicate copy)` --semantically_similar_to--> `Doc Toolkit Router Skill`  [INFERRED] [semantically similar]
  skills/doc-toolkit-router/SKILL.md → .claude/skills/doc-toolkit-router/SKILL.md
- `TargetSizeSearch` --semantically_similar_to--> `jpegli Encoder`  [INFERRED] [semantically similar]
  DOMAIN.md → docs/RESEARCH.md
- `HivisionIDPhotos` --semantically_similar_to--> `PhotoSpec Presets`  [INFERRED] [semantically similar]
  docs/RESEARCH.md → DOMAIN.md
- `N1: Local-Only Privacy` --rationale_for--> `Doc Toolkit Router Skill`  [INFERRED]
  docs/PRD.md → .claude/skills/doc-toolkit-router/SKILL.md
- `Print Sheet Skill` --conceptually_related_to--> `SheetLayoutService`  [INFERRED]
  .claude/skills/print-sheet/SKILL.md → DOMAIN.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Doc Stack (PRD -> HLD -> LLD -> PLAN, DOMAIN as ubiquitous language)** — docs_prd, docs_hld, docs_lld, docs_plan, domain, claude [EXTRACTED 1.00]
- **Target-Size Compression Pipeline** — domain_target_size_algorithm, domain_targetsizesearch, domain_budgetdecomposition, domain_bytebudget, domain_qualityfloor, domain_effectivedpi [EXTRACTED 1.00]
- **Compressor Engine Benchmark and Selection** — domain_pikepdf_engine, domain_pymupdf_engine, domain_ghostscript_engine, docs_analysis_engine_benchmark, docs_prd_n2_agpl_quarantine [EXTRACTED 1.00]

## Communities (56 total, 12 thin omitted)

### Community 0 - "Image Codec & SSIM Adapters"
Cohesion: 0.05
Nodes (62): Object, image context — Pillow adapter for ImageCodec., image context — SSIM quality meter (numpy box-window approximation).  Avoids a s, CompressPdfLossless, InspectDocument, MergePdfs, PdfMerger, pdf context — application use cases. These double as NL tool schemas later. (+54 more)

### Community 1 - "Image Compression Use Cases"
Cohesion: 0.06
Nodes (50): CompressImageLossless, _lowest_floor_quality(), CompressionTarget, EffectiveDpi, ImageCodec, ImageKind, PerceptualScore, QualityMeter (+42 more)

### Community 2 - "Skills & Serving Docs"
Cohesion: 0.06
Nodes (62): Doc Toolkit Router Skill, Passport Photo Skill, Print Sheet Skill, Shrink File Skill, Project Instructions (CLAUDE.md), doc-toolkit MCP Server, tools/cli.sh CLI Entrypoint, Python Lock (darwin-aarch64) (+54 more)

### Community 3 - "Python CLI"
Cohesion: 0.08
Nodes (39): build_engines(), cmd_benchmark(), cmd_compress(), cmd_inspect(), cmd_lossless(), cmd_merge(), cmd_photo(), cmd_sheet() (+31 more)

### Community 4 - "Go CLI & Ghostscript"
Cohesion: 0.09
Nodes (18): fail(), main(), usage(), copyFile(), CompressionResult, CompressionTarget, MediaFile, NewGhostscriptCompressor() (+10 more)

### Community 5 - "Rust Image Infra"
Cohesion: 0.09
Nodes (24): EmbeddedImage, F, HashMap, DssimMeter, ImageCrateCodec, Image, ImageCodec, ImageFormat (+16 more)

### Community 6 - "Rust PDF Domain"
Cohesion: 0.10
Nodes (20): Codec, CompressionRecipe, CompressionResult, CompressionTarget, DocumentCensus, EmbeddedImage, ImageKind, PageRange (+12 more)

### Community 7 - "Go Shared Kernel"
Cohesion: 0.10
Nodes (21): DefaultTarget(), ByteBudget, EffectiveDpi, MediaFile, PerceptualScore, QualityFloor, NewPageRange(), SinglePage() (+13 more)

### Community 8 - "MCP Server Tools"
Cohesion: 0.09
Nodes (23): compose_print_sheet(), compress_lossless(), compress_pdf(), create_passport_photo(), inspect_pdf(), list_photo_specs(), merge_pdfs(), Path (+15 more)

### Community 9 - "Photo Application Tests"
Cohesion: 0.12
Nodes (21): create(), _portrait(), Path, CreatePassportPhoto / ComposePrintSheet — spec conformance (LLD §9)., A synthetic 'person against a wall': gradient bg + dark blob upper-center., test_exif_orientation_is_applied(), test_heic_input_round_trips(), test_low_res_source_warns_and_flags_upscaled() (+13 more)

### Community 10 - "Rust CLI & Kernel"
Cohesion: 0.11
Nodes (14): P, PathBuf, main(), usage(), ByteBudget, EffectiveDpi, MediaFile, Metric (+6 more)

### Community 11 - "FastAPI Endpoints"
Cohesion: 0.23
Nodes (17): BackgroundTasks, FileResponse, compress_lossless(), compress_target(), inspect(), photo(), Path, HTTP API — thin layer over the application use cases (HLD §3).  Run:  .venv/bin/ (+9 more)

### Community 12 - "PDF Lossless Optimizer"
Cohesion: 0.15
Nodes (15): Path, PikepdfStructuralOptimizer, MediaFile, Path, pdf context — lossless structural optimizer (pikepdf, MPL-2.0 — license-clean)., compress(), CompressPdfLossless — page rasters byte-identical pre/post (LLD §9)., A JPEG-in-PDF 'scan' via Pillow's PDF writer (uncompressed xref, no objstm     — (+7 more)

### Community 13 - "Rust lopdf Adapters"
Cohesion: 0.15
Nodes (15): LopdfInspector, LopdfSplitter, NativeCompressor, CompressionResult, CompressionTarget, Compressor, DocumentCensus, MediaFile (+7 more)

### Community 14 - "PhotoRenderer Port"
Cohesion: 0.17
Nodes (10): PhotoRenderer, GuideLine, ImageT, Path, RgbColor, Raster operations for photo production., Decode HEIC/JPG/PNG, apply EXIF orientation, return RGB(A) image., Largest crop of the given aspect ratio, centered as close to anchor         as t (+2 more)

### Community 15 - "Pikepdf Compressor"
Cohesion: 0.16
Nodes (11): CompressionResult, CompressionTarget, MediaFile, Path, _image_kind(), CompressionResult, CompressionTarget, ImageKind (+3 more)

### Community 16 - "Go Domain Services"
Cohesion: 0.18
Nodes (12): AllocateBudget(), DocumentCensus, PerceptualScore, QualityFloor, TestBudgetDecomposition(), TestEffectiveDpiScaleTo(), TestPageRangeValidation(), TestTargetSizeSearchPicksLargestFittingQuality() (+4 more)

### Community 17 - "Rust Ghostscript Adapter"
Cohesion: 0.21
Nodes (10): GhostscriptCompressor, CompressionResult, CompressionTarget, Compressor, Default, MediaFile, Path, Result (+2 more)

### Community 18 - "Go pdfcpu Adapter"
Cohesion: 0.16
Nodes (9): CompressionResult, CompressionTarget, Compressor, DocumentCensus, MediaFile, SplitSpec, NativeCompressor, PdfcpuInspector (+1 more)

### Community 19 - "Sheet Layout Service"
Cohesion: 0.26
Nodes (11): LayoutError, Sheet cannot fit at least one photo., Tile identical photos onto a sheet; leftover space becomes uniform gutters., SheetLayoutService, SheetLayoutService — pure math, exhaustively tested (LLD §9)., test_2x2_on_4x6_is_exactly_6_up_zero_gutter(), test_2x2_on_6x4_landscape_is_3_by_2(), test_gutters_are_uniform_and_grid_is_centered() (+3 more)

### Community 20 - "PDF Use-Case Callables"
Cohesion: 0.23
Nodes (6): CompressionResult, CompressionTarget, DocumentCensus, MediaFile, Path, Returns (merged file, page count).

### Community 21 - "CreatePassportPhoto Use Case"
Cohesion: 0.20
Nodes (6): CreatePassportPhoto, ImageT, Largest quality whose encoding fits max_bytes.          Reuses the shared Target, PhotoSpec, A passport-photo compliance preset. Data, not code., Serialization for /specs, list_photo_specs — one home (W2).

### Community 22 - "Shared Test Fixtures"
Cohesion: 0.20
Nodes (10): api_client(), jpeg_bytes(), portrait(), Path, Shared test fixtures — setup/teardown lives here; test bodies assert business lo, A synthetic 'person against a wall': light bg + dark blob upper-center, 1200×160, Noisy 1200×1600 JPEG bytes (unoptimized Huffman — room for lossless gains)., A 3-page JPEG-in-PDF 'scan' via Pillow's PDF writer (structural slack included). (+2 more)

### Community 23 - "Photo Application Layer"
Cohesion: 0.31
Nodes (8): ComposePrintSheet, PhotoResult, photo context — application use cases.  CreatePassportPhoto: JPG/HEIC → spec-con, SheetResult, FaceLocator, ABC, photo context — ports.  PhotoRenderer is generic over the adapter's opaque image, Where should the crop be centered? Returns fractions of image size (0..1).

### Community 24 - "Go Image Codec"
Cohesion: 0.22
Nodes (4): ImageFormat, PerceptualScore, BoxSsimMeter, XDrawCodec

### Community 25 - "API Round-Trip Tests"
Cohesion: 0.33
Nodes (6): _jpeg_bytes(), HTTP API round-trips via TestClient (LLD §9)., test_lossless_round_trip(), test_photo_round_trip(), test_photo_unknown_spec_is_422(), test_sheet_round_trip()

### Community 26 - "PDF Ports"
Cohesion: 0.29
Nodes (5): CompressionResult, CompressionTarget, DocumentCensus, MediaFile, Path

### Community 27 - "Photo Domain"
Cohesion: 0.33
Nodes (4): photo context — domain layer. Pure: no third-party imports.  Compliance specs ar, A computed tiling of identical photos onto a sheet (SheetLayoutService output)., SheetLayout, photo context — domain services. Pure tiling math, no library imports.

### Community 28 - "Sheet Spec Validation"
Cohesion: 0.29
Nodes (3): ValueError, A print sheet size at a print DPI. 4x6 @ 300 → 1200×1800 px., SheetSpec

### Community 29 - "Numpy SSIM Internals"
Cohesion: 0.40
Nodes (5): ndarray, _box(), _luma(), PerceptualScore, Mean over non-overlapping w x w blocks via cumulative sums (cheap).

### Community 30 - "Fragment: ports.go"
Cohesion: 0.40
Nodes (4): Compressor, PdfCodec, PdfInspector, Splitter

### Community 31 - "Fragment: .__call__()"
Cohesion: 0.40
Nodes (3): GuideLine, Path, Full-bleed cut lines along every cell boundary (both edges of each cell).

### Community 32 - "Fragment: domain.go"
Cohesion: 0.50
Nodes (3): ImageCodec, ImageFormat, QualityMeter

## Knowledge Gaps
- **32 isolated node(s):** `.venv/bin/python`, `pdftoolkit`, `ImageFormat`, `ImageCodec`, `QualityMeter` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ubiquitous Language (DOMAIN.md)` connect `Skills & Serving Docs` to `Rust Ghostscript Adapter`, `Rust Image Infra`, `Rust lopdf Adapters`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `PikepdfCompressor` connect `Python CLI` to `Image Codec & SSIM Adapters`, `Image Compression Use Cases`, `MCP Server Tools`, `FastAPI Endpoints`, `Pikepdf Compressor`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `PhotoRenderer` connect `PhotoRenderer Port` to `Photo Application Tests`, `Photo Application Layer`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `DocumentCensus` (e.g. with `CompressPdfLossless` and `CompressPdfToTarget`) actually correct?**
  _`DocumentCensus` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PikepdfCompressor` (e.g. with `PillowImageCodec` and `NumpySsimMeter`) actually correct?**
  _`PikepdfCompressor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `CompressionResult` (e.g. with `CompressPdfLossless` and `CompressPdfToTarget`) actually correct?**
  _`CompressionResult` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ImageCodec` (e.g. with `CompressImageLossless` and `RecompressOutcome`) actually correct?**
  _`ImageCodec` has 7 INFERRED edges - model-reasoned connections that need verification._