import  json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import argparse

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

    for item in records:
        if not item["text"].strip():
            continue

        ids.append(item["id"])
        texts.append(f"{item['heading']}\n{item['text']}")

    embeddings = model.encode(texts, show_progress_bar=True)

    print(f"Embedded {len(texts)} chunks")
    print(embeddings.shape)