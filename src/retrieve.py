
import chromadb
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
def load(jsonl_path: Path):
    with jsonl_path.open() as f:
        return [json.loads(line) for line in f]
def get_collection():
    client =  chromadb.PersistentClient(path="data/index")
    return  client.get_or_create_collection("cfr_192")
    
def retrieve(question: str, model, collection, k: int =5)->list[dict]:
    # turn question into number (embedding)
    query_embedding = model.encode([question])

    # Chroma's search method, actual retrieval in RAG
    results = collection.query(
        query_embeddings = query_embedding.tolist(),
        n_results = k,
    )

    output = []
    for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
        output.append({
            "citation": meta["citation"],
            "heading": meta["heading"],
            "text":doc,
        })

    return output

if __name__ == "__main__":
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    collection = get_collection()

    for r in retrieve("what pressure is required for a leak test", model, collection):
        print(r["citation"], "-", r["heading"], "\n", r["text"])