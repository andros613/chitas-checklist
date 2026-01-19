#!/usr/bin/env python3
"""Convert calendar JSONL to HTML checklist table."""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert calendar JSONL to HTML checklist table"
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
        help="Output HTML file path (default: stdout)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Chitas Checklist",
        help="Title for the HTML page",
    )
    return parser.parse_args()


def format_short_date(en_date: str) -> str:
    """Convert date like '1/10/2026' or '12/28/2025' to 'Jan 10'."""
    try:
        dt = datetime.strptime(en_date, "%m/%d/%Y")
    except ValueError:
        # Try alternate format without leading zeros
        dt = datetime.strptime(en_date, "%m/%d/%Y".replace("%m", "%m").replace("%d", "%d"))
        parts = en_date.split("/")
        dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]))
    return dt.strftime("%b %d").replace(" 0", " ")


def generate_html(entries: list[dict], title: str) -> str:
    """Generate HTML table from calendar entries."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"UTF-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"  <title>{title}</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }",
        "    h1 { text-align: center; }",
        "    table { border-collapse: collapse; width: 100%; max-width: 900px; margin: 0 auto; }",
        "    th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }",
        "    th { background-color: #f5f5f5; font-weight: 600; }",
        "    tr:nth-child(even) { background-color: #fafafa; }",
        "    tr.shabbat { background-color: #fff8e1; }",
        "    tr.special { background-color: #e3f2fd; }",
        "    .parsha { font-style: italic; }",
        "    .checkbox { width: 60px; text-align: center; }",
        "  </style>",
        "</head>",
        "<body>",
        f"  <h1>{title}</h1>",
        "  <table>",
        "    <thead>",
        "      <tr>",
        "        <th>Hebrew Date</th>",
        "        <th>English Date</th>",
        "        <th>Day</th>",
        "        <th>Special</th>",
        "        <th>Chumash-Rashi</th>",
        "        <th class=\"checkbox\">✓</th>",
        "        <th>Tehillim</th>",
        "        <th class=\"checkbox\">✓</th>",
        "        <th>Tanya</th>",
        "        <th class=\"checkbox\">✓</th>",
        "      </tr>",
        "    </thead>",
        "    <tbody>",
    ]

    for entry in entries:
        he_date = entry.get("he_date", "")
        en_date = entry.get("en_date", "")
        short_date = format_short_date(en_date) if en_date else ""
        parsha = entry.get("parsha") or ""
        day_of_week = entry.get("day_of_week", "")
        special_events = entry.get("special_events", [])

        # Determine row class
        row_class = ""
        if day_of_week == "Shabbat":
            row_class = "shabbat"
        elif special_events:
            row_class = "special"

        class_attr = f' class="{row_class}"' if row_class else ""

        special_display = ", ".join(special_events) if special_events else ""

        # Aliyah number: Sunday=1, Monday=2, ..., Shabbat=7
        day_to_aliyah = {
            "Sunday": 1, "Monday": 2, "Tuesday": 3, "Wednesday": 4,
            "Thursday": 5, "Friday": 6, "Shabbat": 7
        }
        aliyah_num = day_to_aliyah.get(day_of_week)
        chumash_display = f"{parsha}: {aliyah_num}" if parsha and aliyah_num else ""

        html_parts.append(f"      <tr{class_attr}>")
        html_parts.append(f"        <td>{he_date}</td>")
        html_parts.append(f"        <td>{short_date}</td>")
        html_parts.append(f"        <td>{day_of_week}</td>")
        html_parts.append(f"        <td>{special_display}</td>")
        html_parts.append(f"        <td>{chumash_display}</td>")
        html_parts.append("        <td class=\"checkbox\"></td>")
        html_parts.append("        <td></td>")  # Tehillim
        html_parts.append("        <td class=\"checkbox\"></td>")
        html_parts.append("        <td></td>")  # Tanya
        html_parts.append("        <td class=\"checkbox\"></td>")
        html_parts.append("      </tr>")

    html_parts.extend([
        "    </tbody>",
        "  </table>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html_parts)


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

    html_output = generate_html(entries, args.title)

    if args.output:
        args.output.write_text(html_output, encoding="utf-8")
        logger.info(f"Output written to {args.output}")
    else:
        print(html_output)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    logger.info(f"Completed in {minutes}m {seconds:.2f}s")


if __name__ == "__main__":
    main()