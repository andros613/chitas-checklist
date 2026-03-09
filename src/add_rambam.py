#!/usr/bin/env python3
"""Add Rambam daily study chapter to JSONL calendar entries by fetching from chabad.org."""

import argparse
import json
import logging
import time
from pathlib import Path

import cloudscraper
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RAMBAM_BASE_URL = "https://www.chabad.org/dailystudy/rambam.asp"
RAMBAM_FIELD = "rambam_1_ch"

scraper = cloudscraper.create_scraper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Rambam daily study chapter to JSONL calendar entries"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the JSONL file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSONL file path (default: overwrite input file in-place)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Max fetch attempts until all rows are filled (default: 5)",
    )
    return parser.parse_args()


def fetch_rambam_chapter(date: str) -> str | None:
    """Fetch Rambam chapter for a given date from chabad.org.

    Args:
        date: Date in format "M/D/YYYY" (e.g., "3/5/2026")

    Returns:
        Rambam chapter string (e.g., "Talmud Torah - Chapter 2") or None if not found
    """
    try:
        response = scraper.get(RAMBAM_BASE_URL, params={"tdate": date, "rambamChapters": 1}, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch rambam for {date}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    subtitle = soup.find("h2", class_="article-header__subtitle")
    if not subtitle:
        logger.warning(f"No Rambam subtitle found for date {date}")
        return None

    return subtitle.get_text(strip=True)


def main() -> None:
    start_time = time.time()

    args = parse_args()

    if not args.input_file.exists():
        raise ValueError(f"Input file not found: {args.input_file}")

    logger.info(f"Reading {args.input_file}")
    lines = args.input_file.read_text(encoding="utf-8").strip().split("\n")

    entries = []
    for line in lines:
        if line.strip():
            entries.append(json.loads(line))

    logger.info(f"Loaded {len(entries)} entries")

    output_path = args.output if args.output else args.input_file

    for attempt in range(1, args.max_attempts + 1):
        missing = [e for e in entries if not e.get(RAMBAM_FIELD) and e.get("en_date")]
        if not missing:
            logger.info("All entries have rambam")
            break

        logger.info(f"Attempt {attempt}/{args.max_attempts}: {len(missing)} entries missing rambam")

        fetched = 0
        failed = 0

        for entry in entries:
            if entry.get(RAMBAM_FIELD) or not entry.get("en_date"):
                continue

            en_date = entry["en_date"]
            logger.info(f"Fetching Rambam for {en_date}")
            chapter = fetch_rambam_chapter(en_date)

            if chapter:
                entry[RAMBAM_FIELD] = chapter
                fetched += 1
                logger.info(f"  -> {chapter}")
            else:
                failed += 1

            time.sleep(args.delay)

        logger.info(f"Attempt {attempt} stats: {fetched} fetched, {failed} failed")

        output_lines = [json.dumps(entry, ensure_ascii=False) for entry in entries]
        output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        logger.info(f"Output written to {output_path}")

    else:
        still_missing = sum(1 for e in entries if not e.get(RAMBAM_FIELD) and e.get("en_date"))
        if still_missing:
            raise ValueError(f"{still_missing} entries still missing rambam after {args.max_attempts} attempts")

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    logger.info(f"Completed in {minutes}m {seconds:.2f}s")


if __name__ == "__main__":
    main()
