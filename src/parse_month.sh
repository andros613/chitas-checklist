#!/usr/bin/env bash
# Find data/*.htm files containing a month name (outside of TodaysDate/Today is context),
# parse them, filter to that month's entries, and write to a JSONL file.
#
# Usage:   parse_month.sh <month_name> [output_file]
# Example: parse_month.sh Shevat data/5786_11_shevat.jsonl
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <month_name> [output_file]" >&2
    echo "Example: $0 Shevat data/5786_11_shevat.jsonl" >&2
    exit 1
fi

month="$1"
month_lower=$(echo "$month" | tr '[:upper:]' '[:lower:]')
output="${2:-data/${month_lower}.jsonl}"

# Find .htm files in data/ that contain the month name on a line
# that is NOT part of a TodaysDate or "Today is" context.
matching_files=()
for f in data/*.htm; do
    [[ -f "$f" ]] || continue
    if grep -i "$month" "$f" | grep -iv "TodaysDate\|Today is" | grep -qi "$month"; then
        matching_files+=("$f")
    fi
done

if [[ ${#matching_files[@]} -eq 0 ]]; then
    echo "No data files found containing '$month' (outside TodaysDate/Today is)" >&2
    exit 1
fi

echo "Found ${#matching_files[@]} file(s): ${matching_files[*]}" >&2

python src/parse_chabad_month.py "${matching_files[@]}" | fgrep "$month" > "$output"

echo "Output written to $output" >&2
