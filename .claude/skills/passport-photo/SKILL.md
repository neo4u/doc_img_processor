---
name: passport-photo
description: Create US passport, India passport, or OCI-compliant photos from any JPG/HEIC/PNG picture, plus a 4x6 print sheet. Use when the user mentions passport photo, OCI photo, visa photo, photo for application/renewal, or drops a portrait photo asking to make it official.
---

# Passport Photo

Turn any photo (JPG, HEIC from iPhone, PNG) into a compliant passport-style photo
and a ready-to-print 4×6 sheet.

## Choosing the spec

Pick from what the user says — never ask if it's inferable:
- "OCI", "OCI card", "India card for kids" → `india_oci` (enforces ≤ 200 KB)
- "India passport", "Indian passport" → `india_passport`
- "US passport", "passport renewal", "visa", or unspecified → `us_passport`

## Steps

1. Run (from the project root):
   ```bash
   tools/cli.sh photo "<INPUT>" --spec <SPEC>
   ```
   This writes `<input>_<spec>.jpg` **and** `<input>_<spec>_sheet4x6.jpg` next to
   the input. No other flags needed.
2. Relay any `⚠` warnings prominently (e.g. low-resolution source).
3. Tell the user, in plain words:
   - where both files are;
   - the photo meets the digital spec (size/DPI/format) but a human must confirm
     **head position, expression, and background** against the printed notes;
   - the sheet prints at Walgreens/CVS/Costco as a **regular 4×6 photo print**
     (~$0.40) and cuts into 6 passport photos along the gray guide lines.

## Checking compliance notes

```bash
.venv/bin/python -c "from pdf_toolkit.photo_context import PRESETS; print(PRESETS['<SPEC>'].notes)"
```

`tools/cli.sh` bootstraps the venv itself if it's missing — no setup step needed.
