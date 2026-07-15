# doc_img_processor — project instructions

A local, private toolkit for passport photos and document compression. **Nothing
here ever goes to an online service — all processing is on this machine.**

## For everyday use (no technical knowledge needed)

Just say what you want and drag a file into the chat, for example:
- *"Make passport photos from this"* (a phone photo, HEIC is fine)
- *"I need OCI photos for the kids"*
- *"Make a printable sheet of this photo"*
- *"This PDF is too big for the portal, it needs to be under 1 MB"*
- *"Shrink this scan without losing any quality"*

Claude will pick the right skill below, run it, and tell you where the output is.

## Skill routing (for Claude)

| User intent | Skill |
|---|---|
| passport/OCI/visa photo from a picture | `passport-photo` |
| strip/sheet/multiple copies for printing | `print-sheet` |
| compress/shrink/upload-limit/too-big | `shrink-file` |

Rules:
- Prefer skills; they wrap the CLI with the right defaults. Never ask the user for
  flags, DPI, pixels, or specs — infer (OCI → `india_oci`, etc.) and use defaults.
- CLI entrypoint is **`tools/cli.sh`** (self-bootstraps the venv). Hermetic
  alternative: `bazel run //:py_cli -- …` (pass absolute paths; runs from runfiles).
- Outputs land next to the input file; always state the full output path.
- Surface every `⚠` warning the tools print.
- The same operations are exposed as MCP tools (server `doc-toolkit`, see
  `.mcp.json`) — prefer MCP when it's connected, CLI otherwise. Same results,
  with one deliberate exception: Ghostscript escalation on hard-to-compress PDFs
  is CLI-only (served paths stay AGPL-free by design — PRD N2).

## For development

- Doc stack (read in order): `docs/PRD.md` → `docs/HLD.md` → `docs/LLD.md` →
  `docs/PLAN.md`. Ubiquitous language: `DOMAIN.md`. Study notes:
  `docs/OS_CS_ALGOS_PRIMITIVES.md`.
- Before committing: `tools/pre-commit.sh` (ruff, mypy, pytest, gazelle diff).
- Bazel: `bazel run //:venv`, `//:gazelle`, `//:pre-commit`.
- Hard rules live in `DOMAIN.md` §Hard Rules — they are tests, not suggestions.
