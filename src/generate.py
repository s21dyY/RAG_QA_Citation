import requests
import re


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"

NOT_FOUND = "Not found in the provided text."

SYSTEM_PROMPT = f"""
    You will anser questions about 49 CFR Part 192(US gas pipeline safety regulations).

    Rules:
    1. Use ONLY the regulation sections provided. Do not use outside knowledge.
    2. Cite ethe section for every claim in sqare baskets,  e.g.[192.611]
    3. If the provided sections do not answer the question, reply exactly: {NOT_FOUND} 
"""
SECTION_RE = re.compile(r"192\.\d+")

def build_prompt(q:str, chunks: list[dict])->str:
    blocks = []
    for c in chunks:
        blocks.append(f"[{c["citation"]}] {c["heading"]}\n{c["text"]}")
    context = "\n\n----\n\n".join(blocks)
    return f"Context: \n\n{context}\n\n---\n\nQustion:{q}"

def call_llm(prompt:str)->str:
    resp = requests.post(
        OLLAMA_URL, 
        json = {
            "model": MODEL,
            "messages":[
                {
                    "role":"system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt,
                 },
            ],
            # True: llama send word by word response
            "stream": False,

            # num_ctx: tell Ollama dont cutoff block
            # temperature: always get the same answer for the same prompt
            "options": {"num_ctx":16384, "temperature":0}
        })
    return resp.json()["message"]["content"]

def check_ans(ans, chunks):

    # list of all citation number in the anser
    cited = set(SECTION_RE.findall(ans))

    retrieved = set()
    for c in chunks:
        retrieved |= set(SECTION_RE.findall(c["citation"]))

    not_found = NOT_FOUND.lower().rstrip(".") in ans.lower()

    return {
        "cited": sorted(cited & retrieved),
        "unsupported": sorted(cited - retrieved),
        "not_found": not_found,
    }

if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer
    from retrieve import get_collection, retrieve

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    collections = get_collection()

    q ="How deep must a transmission line be buried in a Class 3 location?"
    chunks = retrieve(q, model, collections)
    ans = call_llm(build_prompt(q,chunks))
    print(ans)
    print(check_ans(ans, chunks))


