#!/usr/bin/env bash
# Usage: fetch_month.sh <tdate> <output_file>
# Example: fetch_month.sh 3/1/2026 data/2026_03_mar.htm
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <tdate> <output_file>" >&2
    echo "Example: $0 3/1/2026 data/2026_03_mar.htm" >&2
    exit 1
fi

tdate="$1"
output="$2"

curl -s -L \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    "https://www.chabad.org/calendar/view/month.asp?tdate=${tdate}" \
    -o "$output"

echo "Saved to $output"
