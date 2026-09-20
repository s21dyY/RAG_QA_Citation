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

<!--
Next entry template:

## YYYY-MM-DD — <short description>

**Context:**
**Expected/Found:**
**Investigation:**
**Decision:**
-->
