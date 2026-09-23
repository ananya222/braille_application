# Standalone large Braille stress documents

Generated without production-code changes using fixed seed `20260921`.

Each page contains 26 lines. Each line contains five groups of seven nonblank
6-dot cells separated by four Braille spaces: 39 Braille cells per line and
1,014 cells per page. The PDFs contain no page annotations; the only metadata
present is the standard `/Producer: pypdf` entry from the PDF writer.

| File | Pages | Total cells | Average cells/page | Size |
|---|---:|---:|---:|---:|
| `performance_braille_050_pages.pdf` | 50 | 50,700 | 1,014 | 134,190 bytes |
| `performance_braille_100_pages.pdf` | 100 | 101,400 | 1,014 | 245,865 bytes |
| `performance_braille_250_pages.pdf` | 250 | 253,500 | 1,014 | 580,929 bytes |
| `performance_braille_500_pages.pdf` | 500 | 507,000 | 1,014 | 1,139,502 bytes |

## Verification

- `pypdf` reports exactly 50, 100, 250, and 500 pages respectively.
- The validator's PDF reader extracts exactly the corresponding total cell
  counts and 26 lines per page.
- All extracted Braille code points are in U+2800..U+283F; no 8-dot cells were
  found.
- First, middle, and final pages of every PDF were rendered with Poppler.
  Sampled pages contain 1,014 glyphs, 26 rows, x coordinates 40.0..503.57,
  and no glyph outside the checked page margins.
- No page has `/Annots` entries.

Rendered QA images are under `reports/standalone_large_braille_rendered/`.
