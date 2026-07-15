# doc_image_processor — Bazel-Native Polyglot Migration

## Context
Migrated `~/scripts/pdf_toolkit/` into a Bazel monorepo at `~/personal/doc_image_processor/`.
Three languages (Python reference, Rust partial, Go partial) over one shared DDD
ubiquitous language (`DOMAIN.md`). Goal: publishable, reproducible polyglot build.

**Design principle (per user):** a *mature module structure that needs zero Gazelle
directives.* Every directive we might have used was eliminated by structure instead.

---

## How each Gazelle directive was designed away

| Directive we avoided | Structural decision that removes it |
|---|---|
| `map_kind py_* → aspect_rules_py` | Use **native `rules_python`** rules — Gazelle emits `py_library/py_binary/py_test` with correct loads on its own. |
| `python_root` | **Python package lives at the repo root** (`//pdf_toolkit/…`). Repo root *is* the default import root, so `pdf_toolkit.x` resolves with no marker and no `imports` attr. |
| `python_generation_mode file` | The AGPL adapters live in their **own package** `pdf_toolkit/pdf_context/infrastructure/agpl/`. Package-mode Gazelle isolates them naturally. |
| `prefix` (Go) | `go/go.mod` (`module pdftoolkit`) → Gazelle infers the prefix (module mode). Importpaths come out `pdftoolkit/cli`, `pdftoolkit/pdfcontext`, … |
| `resolve` (third-party py) | Checked-in **`gazelle_python.yaml`** manifest maps `fitz→pymupdf`, `PIL→pillow`, etc. |
| `exclude docs/rust`, `python_test_file_pattern` | Unnecessary — those dirs have no py/go targets; the test pattern is already the default. |

Result: **root `BUILD.bazel` contains no `# gazelle:` directives.**

---

## Final layout

```
~/personal/doc_image_processor/
├── MODULE.bazel            # Bzlmod; all deps + toolchains
├── MODULE.bazel.lock       # committed for reproducibility
├── BUILD.bazel             # gazelle_binary, gazelle, modules_mapping, manifest, aliases
├── .bazelrc  .bazelversion(8.6.0)  .gitignore
├── gazelle_python.yaml     # generated manifest (import→pip dist)
├── DOMAIN.md   docs/ANALYSIS.md   docs/BAZEL_MIGRATION.md (this plan)
│
├── dependencies/python/
│   ├── requirements.in
│   ├── requirements-linux-x86_64.txt      # lock (compiled under py3.13)
│   ├── requirements-darwin-aarch64.txt    # lock (local dev)
│   └── BUILD.bazel                         # exports_files
│
├── pdf_toolkit/            # ← Python package AT REPO ROOT (import root)
│   ├── shared_kernel/
│   ├── pdf_context/        # domain.py, ports.py, services.py, application.py, __init__.py
│   │   └── infrastructure/         # pikepdf_compressor, ghostscript_compressor  (LICENSE-CLEAN)
│   │       └── agpl/               # pymupdf_codec, native_compressor           (AGPL — isolated)
│   ├── image_context/      # domain flattened; ports.py, application.py
│   │   └── infrastructure/ # pillow_codec, ssim_meter
│   └── cli/main.py         # → py_binary //pdf_toolkit/cli:main
│
├── go/  (BUILD marks module root; gazelle fills cli/, pdfcontext/, imagecontext/, sharedkernel/)
└── rust/ (single hand-written BUILD.bazel: rust_library + rust_binary + crate_universe)
```

---

## MODULE.bazel deps (pinned, verified to resolve)

| Module | Version | Notes |
|---|---|---|
| `rules_python` | 1.9.0 | native py rules |
| `rules_python_gazelle_plugin` | 1.9.0 | + `modules_mapping` rule |
| `gazelle` | 0.50.0 | Go + Python BUILD gen |
| `rules_go` | 0.60.0 | Go SDK **1.25.0** (Gazelle tools need Go ≥1.24.12) |
| `rules_rust` | 0.71.3 | crate_universe from `//rust:Cargo.lock` |
| Python toolchain | **3.13** | matches local venv; numpy 2.5.1 needs py≥3.12 |

Targets / aliases: `//pdf_toolkit/cli:main` → `//:py_cli`, `//go/cli:cli` → `//:go_cli`,
`//rust:pdftoolkit_bin` → `//:rust_cli`.

---

## Bootstrap sequence (order matters — reproduce from clean checkout)

```bash
cd ~/personal/doc_image_processor
touch gazelle_python.yaml                       # 1. manifest.update needs the file to pre-exist
bazel run //:gazelle_python_manifest.update     # 2. populate gazelle_python.yaml
bazel run //:gazelle                            # 3. generate all BUILD.bazel files
```

---

## Gotchas resolved during setup (documented so they don't recur)

1. **`//go:go.mod` needs a package** — `go_deps.from_file` resolves the label *before*
   Gazelle runs, so `go/BUILD.bazel` must exist as a package marker (kept, with a comment).
2. **`@pypi//:modules_mapping.json` is not auto-generated in rules_python 1.9** — define a
   `modules_mapping(name="modules_map", wheels=all_whl_requirements)` target and point the
   manifest at `:modules_map`.
3. **numpy 2.5.1 requires Python ≥3.12** — the lock was compiled under local py3.13, so the
   Bazel toolchain must be 3.13 (was 3.11 → resolution failure).
4. **Gazelle 0.50 Go tools require Go ≥1.24.12** — Go SDK pinned to 1.25.0 (1.23.5 failed).
5. **`gazelle_python_manifest.update` needs a pre-existing (even empty) `gazelle_python.yaml`.**

---

## Validation status (2026-07-14)

- ✅ `bazel run //:gazelle_python_manifest.update` — manifest generated (fitz→pymupdf, PIL→pillow).
- ✅ `bazel run //:gazelle` — 13 BUILD files generated; no directives.
- ✅ AGPL isolation verified in generated deps: clean `//pdf_toolkit/pdf_context/infrastructure`
  target pulls only `@pypi//pikepdf`; `agpl` target pulls `@pypi//pymupdf`.
- ✅ Go prefix auto-detection verified: `importpath = "pdftoolkit/cli"` (no `go/` leak).
- ⏳ **PENDING** (paused before running): full `bazel build //...`, `bazel test //go/...`
  (5 existing Go tests), and `bazel run //:py_cli -- compress … --kb 1000` end-to-end.

## Remaining project work (from the original toolkit roadmap — unchanged)
Native Rust/Go engines (#7), golden-file tests (#8), NL tool layer (#9), Web UI (#10).

---

## Verify (once resumed)

```bash
bazel build //...                                  # all languages
bazel test  //go/...                               # 5 existing Go unit tests
bazel run //:py_cli -- compress ~/Downloads/neo_visa.pdf /tmp/out.pdf --kb 1000
bazel run //:go_cli  -- --help
bazel build //:rust_cli
```
