---
name: print-sheet
description: Tile an existing passport-style photo onto a 4x6 or 6x4 inch sheet (6 copies) for printing at Walgreens/CVS/Costco. Use when the user asks for a strip, sheet, printable version, or multiple copies of a passport photo.
---

# Print Sheet

Take an existing passport-style photo (already cropped square, e.g. from the
passport-photo skill or visafoto) and tile it 6-up onto a 4×6" sheet at 300 DPI.

## Steps

1. Run (from the project root):
   ```bash
   tools/cli.sh sheet "<PHOTO>"
   ```
   Options only if the user asks: `--size 6x4` (landscape), `--no-guides`
   (no cut lines), `--photo-in 1.5` (non-standard print size in inches).
2. Output is `<photo>_sheet4x6.jpg` next to the input.
3. Tell the user: upload it to the Walgreens/CVS/Costco photo site (or app) as a
   **standard 4×6 glossy print** — do not let the kiosk "fit" or "fill"; choose
   actual size. Cut along the light-gray lines for 6 finished 2×2" photos.
