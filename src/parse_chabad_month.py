#!/usr/bin/env python3
"""Parse chabad_month.htm and extract calendar data as line-wise JSON."""

import argparse
import json
import logging
import time
from pathlib import Path

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse chabad_month.htm and extract calendar data as line-wise JSON"
    )
    parser.add_argument(
        "input_files",
        type=Path,
        nargs="+",
        help="Path(s) to the HTML file(s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )
    return parser.parse_args()


DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Shabbat"]


def backfill_parsha(entries: list[dict]) -> list[dict]:
    """Backfill parsha from Shabbat to preceding days (Sunday-Friday) of the same week.

    Entries are expected to be in order within each week (Sunday to Shabbat).
    """
    backfilled_count = 0

    for i, entry in enumerate(entries):
        if entry["day_of_week"] == "Shabbat" and entry["parsha"]:
            parsha = entry["parsha"]
            # Look back at preceding days in the same week
            for j in range(1, 7):  # Up to 6 days back (Friday to Sunday)
                prev_idx = i - j
                if prev_idx < 0:
                    break
                prev_entry = entries[prev_idx]
                # Verify it's a weekday before this Shabbat
                expected_day = DAYS_OF_WEEK[6 - j]  # 5=Friday, 4=Thursday, ..., 0=Sunday
                if prev_entry["day_of_week"] != expected_day:
                    break
                if prev_entry["parsha"] is None:
                    prev_entry["parsha"] = parsha
                    backfilled_count += 1

    logger.info(f"Backfilled parsha to {backfilled_count} weekday entries")
    return entries


def parse_chabad_month(html_content: str) -> list[dict]:
    """Parse the HTML and extract calendar entries.

    Returns a list of dicts with keys: en_date, he_date, day_of_week, parsha, special_events
    """
    soup = BeautifulSoup(html_content, "html.parser")

    entries = []

    # Find all table rows containing calendar days
    rows = soup.find_all("tr", class_="row")

    for row in rows:
        # Get all td cells in the row (one per day of week)
        cells = row.find_all("td", class_="item")

        for col_index, td in enumerate(cells):
            expanded_inner = td.find("div", class_="expanded_inner")
            if not expanded_inner:
                continue

            date_attr = expanded_inner.get("date")
            if not date_attr:
                continue

            # Day of week based on column position
            day_of_week = DAYS_OF_WEEK[col_index] if col_index < len(DAYS_OF_WEEK) else None

            # Extract Hebrew date
            hebrew_date_div = expanded_inner.find("div", class_="jewish_date")
            he_date = hebrew_date_div.get_text(strip=True) if hebrew_date_div else ""

            # Extract special events from holidays div
            special_events = []
            holidays_div = expanded_inner.find("div", class_="holidays")
            if holidays_div:
                # Get all divs inside holidays (can be with class="primary" or no class)
                event_divs = holidays_div.find_all("div")
                for event_div in event_divs:
                    event_text = event_div.get_text(strip=True)
                    if event_text:
                        special_events.append(event_text)

            # Extract parsha for Shabbat days
            parsha = None
            if day_of_week == "Shabbat":
                parsha_link = expanded_inner.find("a", href=lambda h: h and "parshah/default.asp" in h)
                if parsha_link:
                    # Get text after the image (parsha name)
                    parsha = parsha_link.get_text(strip=True)

            entries.append({
                "en_date": date_attr,
                "he_date": he_date,
                "day_of_week": day_of_week,
                "parsha": parsha,
                "special_events": special_events,
            })

    return entries


def main() -> None:
    start_time = time.time()

    args = parse_args()

    all_entries = []
    for input_file in args.input_files:
        if not input_file.exists():
            raise ValueError(f"Input file not found: {input_file}")

        logger.info(f"Reading {input_file}")
        html_content = input_file.read_text(encoding="utf-8")

        logger.info("Parsing HTML content")
        entries = parse_chabad_month(html_content)
        logger.info(f"Extracted {len(entries)} calendar entries from {input_file.name}")
        all_entries.extend(entries)

    logger.info(f"Total: {len(all_entries)} calendar entries from {len(args.input_files)} file(s)")
    all_entries = backfill_parsha(all_entries)

    # Output as line-wise JSON (JSONL format)
    output_lines = [json.dumps(entry, ensure_ascii=False) for entry in all_entries]
    output_text = "\n".join(output_lines)

    if args.output:
        args.output.write_text(output_text + "\n", encoding="utf-8")
        logger.info(f"Output written to {args.output}")
    else:
        print(output_text)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    logger.info(f"Completed in {minutes}m {seconds:.2f}s")


if __name__ == "__main__":
    main()
