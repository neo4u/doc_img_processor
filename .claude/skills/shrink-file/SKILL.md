---
name: shrink-file
description: Compress PDFs and images. Lossless mode (identical quality) for JPG/PNG/PDF, or target-size mode to hit a portal upload limit like "under 1 MB". Use when the user says compress, shrink, too big, upload limit, reduce file size.
---

# Shrink File

Two modes — pick from what the user needs:

## A. Portal has a size limit ("must be under 1 MB / 500 KB")

Lossy but perceptually guarded (SSIM ≥ 0.90). PDFs only:
```bash
tools/cli.sh compress "<IN.pdf>" "<OUT.pdf>" --kb <LIMIT_KB>
```

## B. No size target — just make it smaller with zero quality loss

Works on `.pdf`, `.jpg`, `.jpeg`, `.png`:
```bash
tools/cli.sh lossless "<INPUT>"
```
Output is `<input>_lossless.<ext>` next to the input. Pixels/page images are
bit-identical; if the file is already optimal it's copied unchanged (never larger).

## Also available

- Inspect what's inside a PDF: `tools/cli.sh inspect <file-or-dir>`
- Merge PDFs: `tools/cli.sh merge a.pdf b.pdf --output merged.pdf`

Report before → after sizes in plain words ("4.2 MB → 950 KB, looks identical").
