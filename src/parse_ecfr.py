"""
Parse a downloaded eCFR Part XML file into one record per section
(and per appendix), suitable for use as RAG chunks + citations.

Structure of the eCFR XML for a part (confirmed by inspection):
    DIV5[TYPE=PART]
      DIV6[TYPE=SUBPART]
        DIV8[TYPE=SECTION]   N="192.1"  <- one record per DIV8
          HEAD                          <- "§ 192.1 What is the scope..."
          P, TABLE, EXTRACT, ...        <- body content
      DIV9[TYPE=APPENDIX]    N="Appendix A to Part 192"  <- one record per DIV9

Usage:
    python src/parse_ecfr.py data/raw/title-49-part-192_2026-09-17.xml
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# "§ 192.1 What is the scope of this part?" -> section number + heading text
HEAD_SPLIT_RE = re.compile(r"^\s*§\s*([\d.]+[a-z]?)\s+(.*)$")


def clean_text(s: str) -> str:
    s = s.replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def div_body_text(div, head_tag) -> str:
    """All text inside `div` except the HEAD element, in document order."""
    parts = []
    for child in div.find_all(recursive=False):
        if child is head_tag:
            continue
        text = child.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return clean_text("\n\n".join(parts))


def parse_sections(xml_path: Path):
    soup = BeautifulSoup(xml_path.read_bytes(), "lxml-xml")

    part_div = soup.find("DIV5", {"TYPE": "PART"})
    part_number = part_div["N"] if part_div is not None else None

    records = []

    # Sections
    for sec in soup.find_all("DIV8", {"TYPE": "SECTION"}):
        number = sec.get("N", "").strip()
        head = sec.find("HEAD")
        head_text = clean_text(head.get_text(" ", strip=True)) if head else ""

        m = HEAD_SPLIT_RE.match(head_text)
        if m:
            heading = m.group(2)
        else:
            heading = head_text

        body = div_body_text(sec, head)

        records.append(
            {
                "id": f"49-cfr-{number}",
                "type": "section",
                "part": part_number,
                "section_number": number,
                "citation": f"49 CFR {number}",
                "heading": heading,
                "text": body,
            }
        )

    # Appendices
    for app in soup.find_all("DIV9", {"TYPE": "APPENDIX"}):
        number = app.get("N", "").strip()
        head = app.find("HEAD")
        heading = clean_text(head.get_text(" ", strip=True)) if head else number
        body = div_body_text(app, head)

        records.append(
            {
                "id": f"49-cfr-{number}".lower().replace(" ", "-"),
                "type": "appendix",
                "part": part_number,
                "section_number": number,
                "citation": f"{number}, Title 49",
                "heading": heading,
                "text": body,
            }
        )

    return records


def write_outputs(records, stem: str):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    jsonl_path = PROCESSED_DIR / f"{stem}.jsonl"
    with jsonl_path.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    csv_path = PROCESSED_DIR / f"{stem}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "type", "part", "section_number", "citation", "heading", "text"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} records")
    print(f" -> {jsonl_path}")
    print(f" -> {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml_path", type=Path, help="Path to downloaded eCFR part XML file")
    args = parser.parse_args()

    if not args.xml_path.exists():
        print(f"File not found: {args.xml_path}", file=sys.stderr)
        sys.exit(1)

    records = parse_sections(args.xml_path)
    sections = [r for r in records if r["type"] == "section"]
    appendices = [r for r in records if r["type"] == "appendix"]
    print(f"Parsed {len(sections)} sections and {len(appendices)} appendices")

    write_outputs(records, args.xml_path.stem)
