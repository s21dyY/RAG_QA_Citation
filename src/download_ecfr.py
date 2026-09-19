"""
Download a CFR part as XML from the eCFR versioner API and save it, along
with a small metadata sidecar recording the exact date used (regulations
change, so the retrieval date is part of the record for reproducibility).

Usage:
    python src/download_ecfr.py --title 49 --part 192 --date 2026-09-17

Notes:
- The eCFR API requires a date that is <= the title's most recent issue
  date. If you pass a date that's too recent (e.g. "today"), the API
  returns a 404 with a message telling you the latest available date --
  re-run with that date.
- The endpoint requires response compression (Accept-Encoding), which
  the `requests` library sends by default.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def download(title: int, part: int, date: str) -> Path:
    url = f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml?part={part}"
    resp = requests.get(url, timeout=60)

    if resp.status_code != 200:
        print(f"Request failed: HTTP {resp.status_code}", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = RAW_DIR / f"title-{title}-part-{part}_{date}.xml"
    xml_path.write_bytes(resp.content)

    meta = {
        "title": title,
        "part": part,
        "date_requested": date,
        "source_url": url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(resp.content).hexdigest(),
        "size_bytes": len(resp.content),
    }
    meta_path = RAW_DIR / f"title-{title}-part-{part}_{date}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"Saved XML  -> {xml_path} ({len(resp.content):,} bytes)")
    print(f"Saved meta -> {meta_path}")
    print(f"Text as of: {date}")
    return xml_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", type=int, default=49, help="CFR title number")
    parser.add_argument("--part", type=int, default=192, help="CFR part number")
    parser.add_argument(
        "--date",
        required=True,
        help="Issue date to request, YYYY-MM-DD (must be <= title's latest issue date)",
    )
    args = parser.parse_args()
    download(args.title, args.part, args.date)
