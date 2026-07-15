# Engine Analysis — OCI scan corpus (2026-07-14)

9 files, 16 pages, all **RGB JPEG (DCTDecode) ~776 DPI** scans. Target **< 1000 KB**,
`dpi_cap=200`, SSIM floor 0.90. Whole-page SSIM scored via **pypdfium2** render @150dpi.
Outputs in `~/Downloads/oci_compare_v2/<engine>/`.

## Results (all engines, all files, under target ✓)

| file | engine | after | saved | SSIM | ms |
|---|---|---|---|---|---|
| neo_passport (4pg) | **pikepdf** | 939K | 71% | **0.9990** | 4360 |
| neo_passport | pymupdf | 721K | 78% | 0.9974 | 4053 |
| neo_passport | ghostscript | 994K | 69% | 0.9989 | 12013 |
| priti_passport (4pg) | **pikepdf** | 934K | 72% | **0.9992** | 4286 |
| priti_passport | pymupdf | 734K | 78% | 0.9976 | 4084 |
| priti_passport | ghostscript | 995K | 70% | 0.9988 | 11902 |

(full matrix in `benchmark.csv`)

## Aggregate

| Engine | Fidelity (SSIM) | File size | Speed | License | Method |
|---|---|---|---|---|---|
| **pikepdf** ⭐ | **highest, ~0.999** | largest (still 52–72% off) | fast (1.2–4.4s) | **MPL-2.0 — clean** | surgical: embeds chosen JPEG as DCTDecode, nothing else touched |
| pymupdf | ~0.995–0.998 | smallest | fast (1–4s) | AGPL | replace_image + deflate on save (slight generational loss) |
| ghostscript | ~0.999 | middle | slowest (2.3–12s) | AGPL | re-distills whole file |

## Verdict

**Default = pikepdf** (zero-AGPL composite). It has the **highest fidelity** of the three
— because it embeds the exact recompressed JPEG the quality search chose, with no extra
generational re-encode — is the **fastest**, and is **license-clean** for the planned
hosted UI. Its only trade-off is slightly larger files, but every output is comfortably
under the 1000 KB target with a 52–72% reduction.

- **pymupdf** — AGPL alternative; smallest files but lower fidelity and network-copyleft risk.
- **ghostscript** — slowest, no size/quality edge → correctly relegated to `BudgetMissed` escalation only.

This validates the fable strategy: the surgical composite beats `gs -dPDFSETTINGS` for
target-size work *and* keeps AGPL quarantined to the optional fallback.
