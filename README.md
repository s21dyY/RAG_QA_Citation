# RegRAG: cited answers from pipeline-safety regulations

**Status:** in progress. See [SCOPE.md](SCOPE.md) for the full project plan.

**Disclaimer:** this is a demonstration project, not legal or compliance advice.

## Data

**Source:** 49 CFR Part 192 (Transportation of Natural and Other Gas by
Pipeline: Minimum Federal Safety Standards), fetched from the
[eCFR versioner API](https://www.ecfr.gov/developers/documentation/api/v1).

**Text as of: 2026-09-17** (the most recent issue date available from the
API at fetch time — `2026-09-19` was requested first but rejected as later
than the title's latest issue date). Regulations change over time; all
retrieval/eval results in this repo should be read against this date. To
refresh, re-run the download step below with a current date and re-parse.

- Raw XML: [`data/raw/title-49-part-192_2026-09-17.xml`](data/raw/title-49-part-192_2026-09-17.xml)
- Download metadata (URL, timestamp, sha256): [`data/raw/title-49-part-192_2026-09-17.meta.json`](data/raw/title-49-part-192_2026-09-17.meta.json)
- Parsed chunks: [`data/processed/title-49-part-192_2026-09-17.jsonl`](data/processed/title-49-part-192_2026-09-17.jsonl) / `.csv`

## Pipeline (Day 1)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Download the part XML for a given date
python src/download_ecfr.py --title 49 --part 192 --date 2026-09-17

# 2. Parse into one record per section/appendix (the RAG chunks)
python src/parse_ecfr.py data/raw/title-49-part-192_2026-09-17.xml

# 3. Spot-check counts and a few sections against ecfr.gov
python src/verify_sections.py data/processed/title-49-part-192_2026-09-17.jsonl \
    --sections 192.1 192.3 192.13 192.457 192.619
```

### Chunking approach

Each chunk = one regulation section (matches `<DIV8 TYPE="SECTION">` in the
eCFR XML), keyed by section number, with the heading and body kept as
separate fields. Appendices (`<DIV9 TYPE="APPENDIX">`) are included as
their own chunk type. Splitting on this structure (rather than fixed-length
windows) keeps each chunk citable as an exact CFR section.

Record schema (JSONL, one per line):

```json
{
  "id": "49-cfr-192.1",
  "type": "section",
  "part": "192",
  "section_number": "192.1",
  "citation": "49 CFR 192.1",
  "heading": "What is the scope of this part?",
  "text": "(a) This part prescribes minimum safety requirements..."
}
```

### Verification (Part 192, as of 2026-09-17)

- 267 sections + 7 appendices = 274 total chunks.
- 8 sections parse with empty body text — these are legitimate `[Reserved]`
  placeholder sections in the actual regulation (e.g. `192.57`, `192.949`),
  confirmed against the raw XML and ecfr.gov, not a parsing bug.
- Spot-checked `192.1`, `192.3`, `192.13`, `192.457`, `192.619` by hand
  against ecfr.gov — headings and body text match.

### Known limitations

- Tables (`<TABLE>`) are flattened to plain text cell-by-cell, so tabular
  data (e.g. pressure test factor tables) loses its row/column structure
  in the chunk text. Fine for a first pass; revisit if eval shows this
  hurts retrieval/faithfulness on table-heavy sections.
- Cross-references (`<XREF>`) and citations (`<CITA>`) are kept as plain
  text, not resolved into links between chunks.

## Next steps

See the schedule in [SCOPE.md](SCOPE.md): chunking with metadata is done
(Day 1); next is embedding + indexing (Day 2), then the FastAPI retrieval
endpoint (Day 3).
