# Dev notes: debugging & decisions log

Working log of things worth remembering later — why a number came out the way
it did, why a design call was made, and what was ruled out along the way.
This is different from the README (which describes the finished pipeline) and
SCOPE.md (which is the plan) — this is the trail of *how I got there*, kept
so I don't re-litigate the same question twice, and so the eventual "failure
analysis" section of the README has real material to draw from.

**Format per entry:** date, what prompted it, what I found, what I decided
and why.

---

## 2026-09-20 — Reserved-chunk count was 9, not 8

**Context:** Building `build_index.py`, filtering out chunks with empty
`text` before embedding (nothing to retrieve in a `[Reserved]` chunk, and I
want the system to correctly fail to match one — that's the desired
"not found" behavior, not a gap to patch over).

**Expected:** README already documented 8 sections with empty body text
(`192.57`, `192.61`, `192.117-192.119`, `192.123`, `192.191`, `192.478`,
`192.949`, `192.1009`), out of 274 total records. Expected `274 - 8 = 266`
chunks after filtering.

**Found:** Actual filtered count was 265. Printing the skipped ids showed a
9th entry: `49-cfr-appendix-a-to-part-192`.

**Investigation:** Ran
`python src/verify_sections.py data/processed/title-49-part-192_2026-09-17.jsonl --sections "Appendix A to Part 192"`
to print the full record. Heading reads `"Appendix A to Part 192 [Reserved]"`
— confirmed genuinely reserved in the actual regulation (same pattern as the
8 sections, just never checked for appendices before since the original
verification pass in `verify_sections.py` only spot-checked sections).

**Decision:** Not a parsing bug in `parse_ecfr.py` — no fix needed there.
Confirmed 9 empty chunks (8 sections + 1 appendix) is the correct number to
exclude from the vector index. TODO: update the README's "8 sections have
empty body text" line to also mention the reserved appendix, so the two docs
don't disagree.

---

## 2026-09-20 — What text to embed vs. what text to store

**Decision:** Embed `heading + "\n" + text` (so a query matching mostly on
the section's plain-English title, e.g. "definitions", still surfaces the
right chunk), but store the raw `text` alone as the Chroma `document` (this
is what actually gets handed to the LLM as context later — don't want the
heading duplicated awkwardly inside the generation prompt).

**Why it matters:** these two uses of "the text" are different enough
(matching vs. context-for-generation) that conflating them into one field
would have made the retrieval half worse just to make the generation half
slightly simpler.

---

## 2026-09-23 — Generation: prompt fixes and llama3.2:3b vs qwen2.5:7b

**Context:** Day 4, adding `generate.py` (retrieved sections -> Ollama ->
answer with `[192.xxx]` citations, or exactly "Not found in the provided
text."). `check_citations()` compares every section the answer cites against
the sections actually retrieved; a citation outside that set is marked
`unsupported`, and an answer with no valid citation is `grounded: False`.

**Found (5 smoke-test questions, top-5 vector retrieval, temperature 0):**

1. *First prompt (rules in system prompt only), llama3.2:3b:* the model copied
   the context layout instead of answering, e.g. the whole answer to the
   burial-depth question was `[192.327](f)(1)`. For the MAOP question it copied
   the start of 192.619 and stopped at "the lowest of the following:".
2. *Added "answer in your own sentences" + an example answer:* the answers were
   now proper sentences, but citations disappeared (`grounded: False` caught
   it) and burial depth became a false "not found".
3. *Repeated the rules after the question* (small models lose system-prompt
   rules behind ~5 long sections): the citations came back and burial depth was
   correct (36 in. soil / 24 in. rock, 192.327(a)), BUT for the civil-penalty
   question (penalties are in Part 190, not 192) it made up
   "$500,000 / $2.5 million [192.18]". 192.18 was never retrieved -> flagged
   `unsupported`. So the check works, but the model is unsafe.
4. *Same prompt, qwen2.5:7b:* 4/5 correct, both refusals correct, no
   unsupported citations. One miss: false "not found" on burial depth.
   Probable cause: the flattened 192.327 table ("Class 2, 3, and 4 locations
   36 (914) 24 (610)") has no column headers inline (known limitation in
   README).

**Decision:** default to qwen2.5:7b. For a compliance tool, a false refusal is
a much cheaper failure than a confident wrong answer with a citation that
looks real. Cost: ~7-30 s per answer vs ~5-10 s on the 3B (local, M-series).
Keep the model as a parameter so Day 9 can report both.

**Known issues / follow-ups:**
- `APPENDIX_RE` false positive: "Appendix N of ASME B31.8" (an external
  standard cited inside 192.619) gets flagged as an unsupported Part 192
  appendix. Tighten the regex, or only match inside `[...]`.
- Table flattening now has a concrete failure case (192.327). Candidate Day 10
  improvement: render tables as "row: col=value" lines in `parse_ecfr.py`.
- Answerable questions whose table cell loses its headers are a good category
  to include in the 40-question eval set.

---

<!--
Next entry template:

## YYYY-MM-DD — <short description>

**Context:**
**Expected/Found:**
**Investigation:**
**Decision:**
-->
