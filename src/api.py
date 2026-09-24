
from fastapi import FastAPI
from src.retrieve import get_collection, retrieve
from src.generate import call_llm, build_prompt, check_ans
from sentence_transformers import SentenceTransformer

# uvicorn src.api:app --reload
app = FastAPI()
model = None
collection = None

@app.on_event("startup")
def startup():
    global model,collection
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    collection = get_collection()

# give you the determinstic output from ChromaDB indexing
@app.get("/search")
def search(q:str, k:int=5):
    return retrieve(q, model, collection,k)

# Adding LLM layer, now LLM will retrieve anser based on ChromaDB
@app.get("/ask")
def ask(q: str, k: int = 5):
    chunks = retrieve(q, model, collection, k)
    answer = call_llm(build_prompt(q, chunks))
    return {
        "question": q,
        "answer": answer,
        **check_ans(answer, chunks),
        "sources": [c["citation"] for c in chunks],
    }