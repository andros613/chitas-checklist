# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Generates a monthly Chitas (daily Torah study) checklist as a printable PDF. The checklist includes Chumash-Rashi (by aliyah number), Tehillim (by Hebrew date), and Tanya sections for each day of a Hebrew calendar month.

## Pipeline

The full pipeline for producing a monthly PDF:

1. **Parse calendar HTML** — scrape a monthly calendar page from chabad.org into JSONL:
   ```bash
   python src/parse_chabad_month.py data/2026_03_mar.htm -o data/5786_12_adar.jsonl
   ```

2. **Add Tanya sections** — fetch daily Tanya sections from chabad.org and enrich the JSONL:
   ```bash
   python src/add_tanya.py data/5786_12_adar.jsonl -o data/5786_12_adar.jsonl.with_tanya.final
   ```
   Use `--delay` to control request rate (default 1.0s). Already-fetched entries are skipped (idempotent).

3. **Generate HTML** — convert enriched JSONL to an HTML checklist:
   ```bash
   python src/jsonl2html.py data/5786_12_adar.jsonl.with_tanya.final --title 'Chitas Checklist Adar 5786' > data/5786_12_adar.html
   ```
   Use `--short-month` for 29-day Hebrew months (combines Tehillim 140-150 on day 29).

4. **Render PDF** — convert HTML to A4 PDF using weasyprint:
   ```bash
   python src/html2pdf.py data/5786_12_adar.html
   ```

The `run.sh` script demonstrates the last two steps for a completed month.

## Data files

- `data/*.htm` — raw monthly calendar HTML pages downloaded from chabad.org
- `data/*.jsonl` — parsed calendar data (one JSON object per day)
- `data/*.jsonl.with_tanya.final` — enriched JSONL with Tanya sections added
- `data/*.html` — generated HTML checklist
- `data/*.pdf` — final printable output

The `data/` directory is gitignored. `data/delme/` is a scratch area for intermediate work.

## JSONL schema

Each line in a JSONL file is a JSON object:
```json
{
  "en_date": "3/1/2026",
  "he_date": "1 Adar",
  "day_of_week": "Sunday",
  "parsha": "Pekudei",
  "special_events": ["Rosh Chodesh"],
  "tanya": "Likutei Amarim, beginning of Chapter 19"
}
```

`parsha` is set on Shabbat and backfilled to all weekdays in the same week. `tanya` is added by `add_tanya.py`.

## Dependencies

Python 3 with: `beautifulsoup4`, `requests`, `weasyprint`