"""
Sanity-check parsed sections: print counts and a few full records so you
can eyeball them against https://www.ecfr.gov/current/title-49/part-192

Usage:
    python src/verify_sections.py data/processed/title-49-part-192_2026-09-17.jsonl
    python src/verify_sections.py data/processed/title-49-part-192_2026-09-17.jsonl --sections 192.1 192.3 192.13 192.457
"""
import argparse
import json
from pathlib import Path


def load(jsonl_path: Path):
    with jsonl_path.open() as f:
        return [json.loads(line) for line in f]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl_path", type=Path)
    parser.add_argument(
        "--sections",
        nargs="*",
        default=["192.1", "192.3", "192.13"],
        help="section numbers to print in full for manual spot-checking",
    )
    args = parser.parse_args()

    records = load(args.jsonl_path)
    sections = [r for r in records if r["type"] == "section"]
    appendices = [r for r in records if r["type"] == "appendix"]

    print(f"Total records: {len(records)}")
    print(f"  sections:   {len(sections)}")
    print(f"  appendices: {len(appendices)}")

    empty_text = [r["section_number"] for r in sections if not r["text"].strip()]
    if empty_text:
        print(f"\nWARNING: {len(empty_text)} sections have empty body text: {empty_text}")

    by_number = {r["section_number"]: r for r in records}

    print("\n" + "=" * 80)
    for num in args.sections:
        r = by_number.get(num)
        if r is None:
            print(f"\n[{num}] NOT FOUND")
            continue
        print(f"\n[{r['citation']}] {r['heading']}")
        print("-" * 80)
        print(r["text"][:1500] + ("..." if len(r["text"]) > 1500 else ""))
        print("=" * 80)
