
from fastapi import FastAPI
from src.retrieve import get_collection, retrieve
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

@app.get("/search")
def search(q:str, k:int=5):
    return retrieve(q, model, collection,k)