---
name: doc-toolkit-router
description: Route requests about images and documents — passport/OCI/visa photos, PDF/image compression, size limits, print sheets, scans of identity documents — to the best of three paths - the local doc-toolkit MCP tools, ad-hoc code, or clear human instructions when neither can accomplish the goal. Use for any image/document processing request.
---

# Image + Document Toolkit — router

`doc-toolkit` is a **local image + document toolkit** (7 MCP tools): passport/OCI/visa
photos from any picture, PDF compression to a byte target, lossless image/PDF
compression, print sheets, merge, inspect. This skill decides between **three routes**:

```
TOOL   — the toolkit does this, verified
CODE   — ad-hoc sandbox code (Pillow/pikepdf), outside the toolkit's surface
HUMAN  — neither can do it: give precise instructions for what the user must do
```

## When the TOOL is right — the 3-question test

Use the tool iff **all three** are yes:

1. **Is the operation on its surface?** photo-to-spec · PDF-to-size · lossless
   shrink (pdf/jpg/png) · print sheet · merge · inspect. Nothing else.
2. **Is there a verifiable constraint?** bytes, exact dimensions/DPI, compliance
   preset, page counts. The tool *verifies*; ad-hoc code just hopes. (No
   constraint at all → CODE may be equally fine.)
3. **Is the input a local file it can read?** (jpg/heic/png/pdf on disk)

**Overriding rule regardless of route:** identity documents (passports, visas,
birth certificates, ID photos) never go to web services or online "free tools" —
local tool or local code only.

## Decision table

| Request | Route | Why |
|---|---|---|
| Passport/OCI/visa/ID photo from a picture | TOOL `create_passport_photo` | presets enforce px/DPI/background/byte ceiling (OCI ≤ 200 KB); EXIF+HEIC handled |
| "PDF must be under N KB/MB" | TOOL `compress_pdf` | budget solver + quality search; guarantees the target or reports the miss |
| "Smaller without losing quality" | TOOL `compress_lossless` | bit-identical pixels; any re-encode you write is lossy |
| Print copies / 4×6 strip | TOOL `compose_print_sheet` | 6-up @300 DPI with cut guides, kiosk-ready |
| Combine PDFs / what's inside one | TOOL `merge_pdfs` / `inspect_pdf` | tested; inspect gives true effective DPI |
| Rotate, convert format, watermark, crop-to-arbitrary, resize-no-spec | CODE | outside the surface — don't force the tool |
| Lossless webp/avif/tiff, non-photo image work | CODE | toolkit lossless = pdf/jpg/png only |
| User names a specific other method | their method | mention the tool once if clearly superior, then comply |

## When NEITHER works → HUMAN instructions

Detect these early and answer with **numbered, concrete instructions** — do not
run the tool to produce a doomed output, and do not fake capability:

| Situation | What to instruct |
|---|---|
| Source photo can't yield a compliant result: busy/dark background, harsh shadows, glasses, hair over eyes, blurry, head cut off | How to retake: face a window, plain light wall ~0.5 m behind, phone at eye level ~1.2 m away, neutral expression, no glasses; then re-run the tool on the new shot. (Background *replacement* is on the roadmap, not shipped — say so.) |
| Physical-world steps | Exact kiosk/portal steps: upload the sheet as a **standard 4×6 glossy print**, choose "actual size" (never "fit"/"fill"), cut on the gray lines; portal-specific upload fields |
| Compliance judgment calls (head 50–69% of frame, eye line, expression) | The tool sizes the file correctly but a **human must verify** these against the printed notes — show the spec's `notes` and tell the user exactly what to check |
| Content edits: OCR, redaction, removing a shadow/object, background→white | Not shipped (F8/F9 roadmap). Say what IS possible today, what's coming, and the safe manual alternative (never an online editor for identity docs) |
| Target size mathematically unreachable (e.g. 50-page scan under 200 KB) | Explain the floor, propose: split the document, per-section targets, or ask the portal's real limit |

## Posterior check (after any TOOL/CODE run)

1. Output exists, non-trivial. 2. Constraint actually met (size/dims/pages).
3. Surface every tool warning verbatim — they're compliance-relevant.
4. Report before → after honestly. Tool fails **twice** → switch to CODE and say so.
Missed byte budget → report plainly; offer lower target / accept overage / split.
Never silently re-run with degraded settings.
