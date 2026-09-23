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

    # embedding (np array), turn text into number
    # run each string (heading + text) throght MiniLM model and return a list of 265 vectors
    # one vector per chunk, capturing that chunk's mean as coordinates in space
    embeddings = model.encode(texts, show_progress_bar=True)


    # connection to chromadb, save to path
    client = chromadb.PersistentClient(path="data/index")

    # create table cfr1_92 under client
    collection = client.get_or_create_collection("cfr_192")

    # indexing (upsert is a safer add)
    # write everying into collection row by row
    # id[0] goes with embedding[0], documents[0]...etc
    collection.upsert(
                ids=ids,
                embeddings=embeddings.tolist(), 
                documents=documents,
                metadatas=metadatas,
    )

