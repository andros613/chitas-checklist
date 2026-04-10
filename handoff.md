# Handoff — Chitas Checklist session 2026-04-10

## What we worked on

### PDF layout tweaks (`src/jsonl2html.py`)
- Font: `body` and `th, td` both at **11px** (was originally 11px, temporarily lowered and brought back)
- Column widths (current state):
  - `col-hedate`: 60px
  - `col-endate`: 45px
  - `col-day`: 45px
  - `col-special`: 90px
  - `col-chumash`: 90px
  - `col-tehillim`: 50px
  - `col-tanya`: 85px
  - `col-rambam`: 65px
- The real CSS for the PDF is in `jsonl2html.py` (embedded in the HTML). The `html2pdf.py` A4_CSS is additive but lower specificity — font size changes must go in `jsonl2html.py`.

### Website (`web/src/pages/index.astro`)
Three major features added:

**1. English month dates in titles**
- `displayName()` maps Hebrew month slug → approximate Gregorian months + year
- Handles Tevet spanning Dec/Jan across Gregorian years
- Example: `5786_07_nissan.pdf` → "Nissan 5786 (Mar-Apr 2026)"

**2. Sections: Current / Upcoming / Past**
- Uses `Intl.DateTimeFormat('en-u-ca-hebrew', { month: 'long' })` — returns month NAME (e.g. "Nisan"), not a number
- `INTL_TO_SLUG` map bridges Intl names → filename slugs (e.g. "Nisan" → "nissan")
- Current month matched by year+slug; order derived from actual file's `heYear*100+monthNum`
- Upcoming: ascending order (next month first)
- Past: descending order (most recent first), collapsed under `<details>`

**3. Hero image**
- Image: `web/public/temple_from_space_v02.png` (user switched from v01 to v02)
- Hero CSS added to `web/src/styles/global.css` (same pattern as `../niggun-saloon`)
- Title/subtitle rendered as overlay on image

**4. Inline PDF viewer**
- Current month only: `<iframe class="pdf-viewer">` shown always-visible below the row
- Past/upcoming: download button only, no viewer

## Key files
- `src/jsonl2html.py` — HTML generation + CSS (font, column widths)
- `src/html2pdf.py` — WeasyPrint PDF rendering (A4_CSS; note: lower specificity than inline HTML CSS)
- `web/src/pages/index.astro` — full website logic + markup
- `web/src/styles/global.css` — shared CSS including hero + pdf-list styles
- `web/src/layouts/Layout.astro` — site shell (header, footer)

## Pending / known issues
- None open at end of session
- The `get_rambam_header_and_rest()` function in `jsonl2html.py` had debug `logger.info` lines added mid-session (user edits); may want to clean up
