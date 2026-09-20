import  json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import argparse
import chromadb

def load(jsonl_path: Path):
    with jsonl_path.open() as f:
        return [json.loads(line) for line in f]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl_path", type=Path)
    args = parser.parse_args()
    records = load(args.jsonl_path)

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    ids = []
    texts = []
    documents = []
    metadatas = []

    for item in records:
        if not item["text"].strip():
            continue
        
        ids.append(item["id"])
        texts.append(f"{item['heading']}\n{item['text']}")

        documents.append(item['text'])
        metadatas.append({
            "citation": item["citation"],
            "heading": item["heading"],
            "section_number": item["section_number"],
            "type": item["type"],  
        })

    embeddings = model.encode(texts, show_progress_bar=True)

    client = chromadb.PersistentClient(path="data/index")
    collection = client.get_or_create_collection("cfr_192")
    collection.upsert(
                ids=ids,
                embeddings=embeddings.tolist(),   # Chroma wants plain lists, not a numpy array
                documents=documents,
                metadatas=metadatas,
    )

    print(f"Embedded {len(texts)} chunks")
    print(embeddings.shape)
    print(f"Indexed {collection.count()} chunks into data/index")
