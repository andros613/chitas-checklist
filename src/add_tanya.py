#!/usr/bin/env python3
"""Add Tanya daily study sections to JSONL calendar entries by fetching from chabad.org."""

import argparse
import json
import logging
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TANYA_URL_TEMPLATE = "https://www.chabad.org/dailystudy/tanya.asp?tdate={date}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Tanya daily study sections to JSONL calendar entries"
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
        help="Output JSONL file path (default: stdout)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    return parser.parse_args()


def fetch_tanya_section(date: str) -> str | None:
    """Fetch Tanya section for a given date from chabad.org.

    Args:
        date: Date in format "M/D/YYYY" (e.g., "1/21/2026")

    Returns:
        Tanya section string or None if not found
    """
    url = TANYA_URL_TEMPLATE.format(date=date)

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the h2 with class "article-header__subtitle"
    subtitle = soup.find("h2", class_="article-header__subtitle")
    if not subtitle:
        logger.warning(f"No Tanya subtitle found for date {date}")
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

    # Track fetch statistics
    fetched = 0
    failed = 0
    skipped = 0

    for i, entry in enumerate(entries):
        # Skip if tanya field already exists and is not null/empty
        existing_tanya = entry.get("tanya")
        if existing_tanya:
            logger.info(f"Entry {i + 1}/{len(entries)} already has tanya, skipping")
            skipped += 1
            continue

        en_date = entry.get("en_date", "")
        if not en_date:
            logger.warning(f"Entry {i} has no en_date, skipping")
            skipped += 1
            continue

        logger.info(f"Fetching Tanya for {en_date} ({i + 1}/{len(entries)})")
        tanya_section = fetch_tanya_section(en_date)

        if tanya_section:
            entry["tanya"] = tanya_section
            fetched += 1
            logger.info(f"  -> {tanya_section}")
        else:
            failed += 1

        # Rate limiting - only after making a request
        time.sleep(args.delay)

    logger.info(f"Fetch stats: {fetched} fetched, {failed} failed, {skipped} skipped")

    # Output as JSONL
    output_lines = [json.dumps(entry, ensure_ascii=False) for entry in entries]
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