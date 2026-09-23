# RAG pipeline guide: concepts + the 14-day plan

This is the "what does each piece mean and why" companion to [SCOPE.md](SCOPE.md)
(the plan) and [README.md](README.md) (the finished pipeline's usage docs).
Read this when a term is fuzzy or you want to see how a given day's work fits
into the whole system. [NOTES.md](NOTES.md) has the blow-by-blow debugging
log if you want to see real examples of these concepts going wrong and
getting fixed.

## Part 1 — RAG in one page

**The problem:** an LLM asked "what does the regulation say about X" will
either (a) not know, or (b) confidently make something up. Neither is
acceptable when the answer needs to be trustworthy enough to act on.

**The fix, RAG (Retrieval-Augmented Generation):** instead of asking the LLM
to answer from memory, you find the actual relevant text first, hand it to
the LLM as context, and instruct it to answer *only* from that text. Three
stages:

1. **Retrieval** — given a question, find the small number of document
   chunks most likely to contain the answer, out of all the chunks you have.
2. **Augmentation** — insert those chunks into the prompt you send the LLM,
   alongside the question and your instructions (e.g. "cite the section
   number, say 'not found' if the text doesn't cover this").
3. **Generation** — the LLM produces an answer grounded in exactly that
   text, with a citation pointing back to where it came from.

The system is only as good as retrieval — if the wrong chunk gets retrieved,
no amount of prompt engineering saves the answer. That's why your project
spends so much of its 14 days (Days 5, 8, 9) specifically measuring and
improving retrieval, rather than the LLM step.

## Part 2 — Concepts that are easy to mix up

### Embedding vs. indexing (the one you asked about)

These sound similar but answer different questions:

- **Embedding** answers: *"how do I turn one piece of text into numbers?"*
  A model (`sentence-transformers/all-MiniLM-L6-v2` in your case) reads a
  chunk of text and outputs a vector — a fixed-length list of numbers (384
  of them, for this model) — positioned in space such that texts with
  similar meaning end up as nearby vectors. This happens **once per chunk**,
  independently, chunk by chunk.

- **Indexing** answers: *"given hundreds/thousands of these vectors, how do
  I store them so I can quickly find the closest ones to a new vector
  later?"* This is a storage + search-structure problem, not a
  text-understanding problem. Chroma (your vector store) is what does this
  — it takes the embeddings you already computed and organizes them (plus
  the citation/heading/text you attached as metadata) so that a future
  query can ask "what are the 5 closest chunks to this new vector?" and get
  an answer fast.

**Analogy:** embedding is assigning GPS coordinates to every building in a
city (one-time, per building). Indexing is building the map data structure
that lets you instantly answer "what's within 2 miles of here?" without
checking every single building's distance one by one. You need both — the
coordinates are useless without a way to search them, and the search
structure has nothing to organize without the coordinates.

In `build_index.py`, this is literally two separate lines: `model.encode()`
is the embedding step, `collection.upsert()` is the indexing step.

### Other terms worth pinning down

| Term | Meaning |
|---|---|
| **Chunk** | One retrievable unit of text — in your project, one CFR section or appendix (see `parse_ecfr.py`). |
| **Chunking** | The decision of *how* to split a document into chunks. You chunk by regulatory structure (one section = one chunk), not fixed-length windows — keeps every chunk exactly citable. |
| **Vector store / vector database** | A database specialized for storing embeddings and doing similarity search (Chroma, FAISS, etc.). |
| **Semantic / vector search** | Retrieval based on embedding similarity — finds chunks with *similar meaning*, even if they don't share exact words. |
| **BM25 / keyword search** | Classic search based on word overlap (like a smarter grep). Finds exact term matches (e.g. "192.13" or a specific PSI number) that semantic search can sometimes miss. |
| **Hybrid retrieval** | Combining semantic search and BM25 (e.g. by merging/re-ranking both result lists), aiming to catch what each misses alone. This is your Day 5 task. |
| **Augmentation** | Building the prompt that includes the retrieved chunks + the question + your instructions, before sending it to the LLM. |
| **Generation** | The LLM producing the final answer text, from that augmented prompt. |
| **Faithfulness / groundedness** | Whether the generated answer only says things actually present in the retrieved text — the opposite of hallucination. |
| **Recall@5** | Of your test questions, what fraction had the *correct* chunk somewhere in the top 5 retrieved results? Measures retrieval, not generation. |
| **MRR (Mean Reciprocal Rank)** | Like recall@5, but also rewards the correct chunk showing up *higher* (rank 1 scores better than rank 5). |
| **Refusal rate** | On your 10 unanswerable questions, how often the system correctly said "not found" instead of guessing. |

## Part 3 — The 14-day plan, with concepts attached

Status as of 2026-09-21: Day 1 done, Day 2 in progress.

| Day | Task | Concepts in play | Files |
|---|---|---|---|
| 1 ✅ | Download and parse the regulation into one chunk per section | Chunking by structure, reproducibility (versioned source + hash) | `download_ecfr.py`, `parse_ecfr.py`, `verify_sections.py` |
| 2 🔧 | Chunking with metadata; embed and index | **Embedding**, **indexing**, vector stores | `build_index.py` |
| 3 | Basic retrieval + FastAPI endpoint | Turning "query the index" into an HTTP API; top-k semantic search | new: e.g. `api.py` |
| 4 | Generation step with citations + "not found" rule | Augmentation, prompt design, faithfulness constraint | new: e.g. `generate.py`, Ollama integration |
| 5 | Add BM25 + hybrid retrieval | Keyword search, hybrid ranking, comparing retrieval strategies | new: e.g. `bm25.py`, changes to retrieval |
| 6–7 | Write 40 questions + answer key (30 answerable, 10 not) | Designing an eval set that actually tests refusal, not just lookup | new: e.g. `eval/questions.jsonl` |
| 8 | Build the eval script | Recall@5, MRR — turning "does it work" into a number | new: e.g. `eval/run_eval.py` |
| 9 | Run all 4 configs (vector-only, BM25-only, hybrid, hybrid+different chunk size); mark faithfulness/citations | Comparative evaluation, honest measurement | results table |
| 10 | Failure analysis + one concrete improvement | Root-causing real failures (this is what `NOTES.md` is for) | `NOTES.md`, README updates |
| 11 | Small user test (3-4 people, median time, cost/query) | Business-impact framing, not just accuracy | — |
| 12–13 | README, results table, architecture diagram, cleanup | Communicating the work | `README.md` |
| 14 | Publish to GitHub, add to CV/LinkedIn | — | — |

## Part 4 — How the pieces fit together end to end

```
data/raw/*.xml                (download_ecfr.py)
      |
      v
data/processed/*.jsonl        (parse_ecfr.py — one record per section/appendix)
      |
      +--> spot-check by hand  (verify_sections.py)
      |
      v
embed each chunk's text       (build_index.py: model.encode — Part 2's "embedding")
      |
      v
data/index/  (Chroma)         (build_index.py: collection.upsert — Part 2's "indexing")
      |
      | <-- at query time -->
      v
embed the user's question, search the index for top-k chunks
      |
      v
[Day 5] merge with BM25 keyword results -> hybrid ranked list
      |
      v
[Day 4] build a prompt: instructions + question + retrieved chunk text
      |
      v
[Day 4] LLM (Ollama) generates an answer, citing the section number,
        or says "not found in the provided text"
      |
      v
[Day 3] all of the above wrapped behind a FastAPI endpoint
      |
      v
[Days 6-11] evaluated against 40 known questions -> recall@5, MRR,
            faithfulness, refusal rate, real user timing
```

Everything above the first "at query time" line happens **once, offline**
(you don't re-embed the whole regulation every time someone asks a
question). Everything below it happens **every time a question comes in**.
That split — expensive one-time indexing vs. cheap per-query retrieval — is
the core efficiency idea that makes RAG practical at all.
