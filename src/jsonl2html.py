#!/usr/bin/env python3
"""Convert calendar JSONL to HTML checklist table."""

import argparse
import json
import logging
import re
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
    parser.add_argument(
        "--short-month",
        action="store_true",
        help="Use combined Tehillim 140-150 for day 29 (for 29-day months)",
    )
    return parser.parse_args()


# Tehillim monthly schedule: day of Hebrew month -> Psalm range
TEHILLIM_SCHEDULE = {
    1: "1-9",
    2: "10-17",
    3: "18-22",
    4: "23-28",
    5: "29-34",
    6: "35-38",
    7: "39-43",
    8: "44-48",
    9: "49-54",
    10: "55-59",
    11: "60-65",
    12: "66-68",
    13: "69-71",
    14: "72-76",
    15: "77-78",
    16: "79-82",
    17: "83-87",
    18: "88-89",
    19: "90-96",
    20: "97-103",
    21: "104-105",
    22: "106-107",
    23: "108-112",
    24: "113-118",
    25: "119:\n1-96",
    26: "119:\n97-176",
    27: "120-134",
    28: "135-139",
    29: "140-144",
    30: "145-150",  # On 29-day months, this is recited on day 29
}


def get_tehillim_for_day(he_date: str, short_month: bool = False) -> str:
    """Get Tehillim portion for a Hebrew date like '1 Shevat' or '15 Tevet'.

    If short_month is True, day 29 returns '140-150' (combined day 29+30).
    """
    if not he_date:
        return ""
    # Extract the day number from the beginning of the Hebrew date
    parts = he_date.split()
    if not parts:
        return ""
    try:
        day_num = int(parts[0])
    except ValueError:
        return ""
    if short_month and day_num == 29:
        return "140-150"
    return TEHILLIM_SCHEDULE.get(day_num, "")


def get_tanya_book_name(tanya: str) -> str:
    """Extract book name from tanya string (e.g., 'Likutei Amarim' from 'Likutei Amarim, middle of Chapter 19')."""
    if not tanya:
        return ""
    # Book name is everything before the first comma
    if "," in tanya:
        return tanya.split(",")[0].strip()
    return tanya.strip()


def abbreviate_tanya(tanya: str, prev_book_name: str = "") -> str:
    """Abbreviate Tanya section text for display.

    If prev_book_name matches current book name, drop the book name entirely.
    """
    if not tanya:
        return ""

    current_book = get_tanya_book_name(tanya)
    result = tanya

    # If same book as previous row, drop the book name
    if current_book and current_book == prev_book_name:
        # Remove "BookName, " from the beginning
        result = result.replace(f"{current_book}, ", "")

    result = result.replace("Chapter", "Ch.")
    result = result.replace("beginning", "beg.")
    result = result.replace("middle", "mid.")
    result = result.replace(" of ", " ")
    return result


def abbreviate_rambam(rambam: str, prev_header: str = "") -> str:
    """Abbreviate Rambam chapter text for display.

    Replaces 'Chapter' with 'Ch.' and drops the header name if same as previous row,
    replacing it with '""'.
    """
    if not rambam:
        return ""
    rambam = rambam.replace("Chapter", "Ch.")
    rambam = rambam.replace(" - ", ": ")
    rambam = rambam.replace(" and ", " & ")
    if ": " in rambam:
        header, rest = rambam.rsplit(": ", 1)
        if header == prev_header:
            return f'"" {rest}'
    return rambam


def get_rambam_header_and_rest(rambam: str) -> tuple[str, str]:
    """Extract the header (book/section name) from a Rambam string."""
    rambam = rambam.replace("Chapter", "Ch.")
    rambam = rambam.replace(" - ", ": ")
    rambam = rambam.replace(" and ", " & ")
    if ": " in rambam:
        return rambam.rsplit(": ", 1)
    return rambam, None


_WORD_TO_NUM = {
    "One": "1", "Two": "2", "Three": "3", "Four": "4", "Five": "5",
    "Six": "6", "Seven": "7", "Eight": "8", "Nine": "9",
}


def abbreviate_special_events(events: list[str]) -> list[str]:
    """Abbreviate special event list, combining Omer day + Tonight Count into one entry.

    e.g. ['Passover', 'Omer: Day Three', 'Tonight Count 4']
      -> ['Passover', 'Omer: 3 (Count 4)']
    """
    omer = next((e for e in events if e.startswith("Omer:")), None)
    tonight = next((e for e in events if e.startswith("Tonight Count")), None)

    if not omer:
        return events

    day_str = omer.split("Day ", 1)[1].strip() if "Day " in omer else omer.split(":", 1)[1].strip()
    for word, num in _WORD_TO_NUM.items():
        day_str = day_str.replace(word, num)

    if tonight:
        count = re.search(r"\d+", tonight)
        combined = f"Omer: Day {day_str} (Tonight Count {count.group()})" if count else f"Omer: Day {day_str}"
    else:
        combined = f"Omer: Day {day_str}"

    return [combined if e == omer else e for e in events if e != tonight]


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


def generate_html(entries: list[dict], title: str, short_month: bool = False) -> str:
    """Generate HTML table from calendar entries."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"UTF-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"  <title>{title}</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 4px 10px; font-size: 11px; }",
        "    h1 { text-align: center; font-size: 16px; margin-bottom: 2px; }",
        "    table { border-collapse: collapse; width: 100%; max-width: 900px; margin: 0 auto; table-layout: fixed; }",
        "    th, td { border: 1px solid #ccc; padding: 3px 5px; text-align: left; overflow: hidden; font-size: 11px; }",
        "    th { background-color: #f5f5f5; font-weight: 600; }",
        "    tr:nth-child(even) { background-color: #fafafa; }",
        "    tr.shabbat { background-color: #fff3cd; font-weight: 500; }",
        "    tr.special { background-color: #e3f2fd; }",
        "    .parsha { font-style: italic; }",
        "    .checkbox { width: 15px; text-align: center; }",
        "    .col-hedate { width: 60px; }",
        "    .col-endate { width: 45px; }",
        "    .col-day { width: 45px; }",
        "    .col-special { width: 90px; }",
        "    .col-chumash { width: 90px; }",
        "    .col-tehillim { width: 50px; }",
        "    .col-tanya { width: 85px; }",
        "    .col-rambam { width: 65px; }",
        "    .bh { position: absolute; top: 10px; right: 20px; font-size: 18px; }",
        "    .license { margin-top: 5px; text-align: center; font-size: 12px; color: #666; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class=\"bh\">ב״ה</div>",
        f"  <h1>{title}</h1>",
        "  <table>",
        "    <thead>",
        "      <tr>",
        "        <th class=\"col-hedate\">Hebrew Date</th>",
        "        <th class=\"col-endate\">English Date</th>",
        "        <th class=\"col-day\">Day</th>",
        "        <th class=\"col-special\">Special</th>",
        "        <th class=\"col-chumash\">Chumash-Rashi</th>",
        "        <th class=\"checkbox\">✓</th>",
        "        <th class=\"col-tehillim\">Tehillim</th>",
        "        <th class=\"checkbox\">✓</th>",
        "        <th class=\"col-tanya\">Tanya</th>",
        "        <th class=\"checkbox\">✓</th>",
        "        <th class=\"col-rambam\">Rambam 1 Ch.</th>",
        "        <th class=\"checkbox\">✓</th>",
        "      </tr>",
        "    </thead>",
        "    <tbody>",
    ]

    prev_tanya_book = ""
    prev_rambam_header = ""
    prev_parsha = ""

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

        special_display = ", ".join(abbreviate_special_events(special_events)) if special_events else ""

        # Aliyah number: Sunday=1, Monday=2, ..., Shabbat=7
        day_to_aliyah = {
            "Sunday": 1, "Monday": 2, "Tuesday": 3, "Wednesday": 4,
            "Thursday": 5, "Friday": 6, "Shabbat": 7
        }
        # Abbreviate day names
        day_abbrev = {
            "Sunday": "Sun", "Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed",
            "Thursday": "Thu", "Friday": "Fri", "Shabbat": "Shabbat"
        }
        aliyah_num = day_to_aliyah.get(day_of_week)
        if parsha and aliyah_num:
            parsha_label = '"" ' if parsha == prev_parsha else f"{parsha}: "
            chumash_display = f"{parsha_label}{aliyah_num}"
        else:
            chumash_display = ""
        prev_parsha = parsha
        tehillim_display = get_tehillim_for_day(he_date, short_month)
        tanya_raw = entry.get("tanya") or ""
        tanya_display = abbreviate_tanya(tanya_raw, prev_tanya_book)
        prev_tanya_book = get_tanya_book_name(tanya_raw)
        day_display = day_abbrev.get(day_of_week, day_of_week)

        html_parts.append(f"      <tr{class_attr}>")
        html_parts.append(f"        <td>{he_date}</td>")
        html_parts.append(f"        <td>{short_date}</td>")
        html_parts.append(f"        <td>{day_display}</td>")
        html_parts.append(f"        <td>{special_display}</td>")
        html_parts.append(f"        <td>{chumash_display}</td>")
        html_parts.append("        <td class=\"checkbox\">☐</td>")
        html_parts.append(f"        <td>{tehillim_display}</td>")
        html_parts.append("        <td class=\"checkbox\">☐</td>")
        html_parts.append(f"        <td>{tanya_display}</td>")
        html_parts.append("        <td class=\"checkbox\">☐</td>")
        rambam_raw = entry.get("rambam_1_ch") or ""
        rambam_display = abbreviate_rambam(rambam_raw, prev_rambam_header)
        prev_rambam_header, _ = get_rambam_header_and_rest(rambam_raw)
        html_parts.append(f"        <td>{rambam_display}</td>")
        html_parts.append("        <td class=\"checkbox\">☐</td>")
        html_parts.append("      </tr>")

    html_parts.extend([
        "    </tbody>",
        "  </table>",
        "  <div class=\"license\">",
        "    <p><strong>CC BY-SA 4.0</strong> - This work is licensed under the "
        "Creative Commons Attribution-ShareAlike 4.0 International License. "
        # "You are free to share and adapt this material, provided you give appropriate credit and distribute your "
        # "contributions under the same license. "
        "Data from Chabad.org. "
        "Created with the help of Claude Code. "
        "Amichai Andy Rosenbaum &lt;andros613@proton.me&gt;</p>",
        "  </div>",
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

    html_output = generate_html(entries, args.title, args.short_month)

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