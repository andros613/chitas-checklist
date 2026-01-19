#!/usr/bin/env python3
"""Convert HTML checklist to PDF formatted for A4 paper."""

import argparse
import logging
import time
from pathlib import Path

from weasyprint import HTML, CSS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HTML checklist to PDF formatted for A4 paper"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the HTML file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PDF file path (default: input filename with .pdf extension)",
    )
    return parser.parse_args()


# CSS to ensure proper A4 formatting
A4_CSS = CSS(string="""
    @page {
        size: A4;
        margin: 10mm;
    }

    body {
        font-size: 9pt;
    }

    table {
        width: 100%;
        font-size: 8pt;
        table-layout: fixed;
    }

    th, td {
        padding: 3px 4px;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .checkbox {
        width: 20px;
        min-width: 20px;
        max-width: 20px;
    }

    h1 {
        font-size: 14pt;
        margin-bottom: 8px;
    }

    .license {
        font-size: 7pt;
        margin-top: 15px;
    }

    .bh {
        font-size: 12pt;
    }
""")


def convert_html2pdf(input_path: Path, output_path: Path) -> None:
    """Convert HTML file to PDF with A4 formatting."""
    logger.info(f"Converting {input_path} to PDF")

    html = HTML(filename=str(input_path))
    html.write_pdf(str(output_path), stylesheets=[A4_CSS])

    logger.info(f"PDF written to {output_path}")


def main() -> None:
    start_time = time.time()

    args = parse_args()

    if not args.input_file.exists():
        raise ValueError(f"Input file not found: {args.input_file}")

    output_path = args.output
    if output_path is None:
        output_path = args.input_file.with_suffix(".pdf")

    convert_html2pdf(args.input_file, output_path)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    logger.info(f"Completed in {minutes}m {seconds:.2f}s")


if __name__ == "__main__":
    main()