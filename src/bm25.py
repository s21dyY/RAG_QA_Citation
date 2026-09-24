import re
from rank_bm25 import BM25Okapi
from retrieve import retrieve
# keeps detailed section "192.327" as one token instead of splitting it into "192" and "327"

TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*")
SECTION_RE = re.compile(r"192\.\d+")

def tokenize(text:str)-> list[str]:
    return TOKEN_RE.findall(text.lower())

def build_bm25(collection):
    # reuse the 265 chunks already in Chroma, so both searches cover the same set
    data = collection.get(include=["documents", "metadatas"])
    chunks = []
    for meta, doc in zip(data["metadatas"], data["documents"]):
        chunks.append({"citation": meta["citation"], "heading": meta["heading"], "text": doc})

    # heading + text, same as what you embed (see NOTES 2026-09-20)
    corpus = [tokenize(c["heading"] + "\n" + c["text"]) for c in chunks]
    return BM25Okapi(corpus), chunks

def bm25_search(question: str, bm25, chunks, k: int = 5) -> list[dict]:
    scores = bm25.get_scores(tokenize(question))
    top = scores.argsort()[::-1][:k]
    return [chunks[i] for i in top]


def hybrid_retrieve(question, model, collection, bm25, chunks, k=5, pool=20, rrf_k=60):
    vec = retrieve(question, model, collection, pool)
    kw = bm25_search(question, bm25, chunks, pool)

    scores, by_cite = {}, {}
    for results in (vec, kw):
        for rank, c in enumerate(results, start=1):
            scores[c["citation"]] = scores.get(c["citation"], 0) + 1 / (rrf_k + rank)
            by_cite[c["citation"]] = c

    best = sorted(scores, key=scores.get, reverse=True)[:k]
    # exact lookup: a section named in the question always goes first
    by_num = {c["citation"].split()[-1]: c for c in chunks}
    named = [f"49 CFR {n}" for n in SECTION_RE.findall(question) if n in by_num]
    for cite in named:
        by_cite[cite] = by_num[cite.split()[-1]]
    best = named + [c for c in best if c not in named]
    return [by_cite[cite] for cite in best[:k]]

if __name__ == "__main__":

    from sentence_transformers import SentenceTransformer
    from retrieve import get_collection, retrieve

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    collections = get_collection()

    q = "How deep must a transmission line be buried in a Class 3 location?"
    bm25, chunk = build_bm25(collections)
    
    chunks = retrieve(q, model, collections)
    print(hybrid_retrieve(q, model,collections, bm25, chunk))