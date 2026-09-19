# Project plan: standards Q&A with citations
**Working title:** *RegRAG: cited answers from pipeline-safety regulations*

## 1. The problem and the claim
Engineers and compliance staff lose time searching long regulations, and an answer without a source is a liability. The system answers with the exact section cited, and says "not found" when the text doesn't cover the question. 

## 2. Scope (keep it tight)
- **Documents:** one document family only. In this project, I use **49 CFR Part 192** (US natural gas pipeline safety), from the eCFR website, since US federal regulations are public and structured by section. 
- **Size:** about 200 to 500 pages.
- **Out of scope:** multi-document families.
- **Disclaimer in the README:** it's a demonstration, not legal or compliance advice.

## 3. Tools (all free)
- **Language and API:** Python and FastAPI.
- **Chunking:** by regulation section, with section number and title kept as metadata. Splitting on structure is better than fixed-length splitting for regulations.
- **Embeddings:** an open-source sentence-transformers model.
- **Vector store:** FAISS or Chroma.
- **Keyword search:** BM25 (the `rank_bm25` library).
- **Generation:** a small local model through Ollama, which you already know.
- **Prompt rule:** answer only from the retrieved sections, cite the section numbers, and say "not found in the provided text" otherwise.

## 4. Evaluation (the part that sets it apart)
Write **40 questions** yourself, with the correct section for each:
- **30 answerable**, mixing direct lookups ("what does section X require for...?") and questions that need two sections.
- **10 unanswerable**, whose answer isn't in the text, to test whether the system refuses.

**Compare four configurations:** vector-only, BM25-only, hybrid, and hybrid with a different chunk size.

**Metrics:**
- **Retrieval:** recall@5 and MRR (did the right section appear, and how high?).
- **Citation accuracy:** did the cited section actually support the answer?
- **Faithfulness:** did the answer add anything not in the retrieved text? You can reuse your Outlier rubric approach here, marking each answer by hand and, if you like, comparing it with an LLM judge to see how far they agree.
- **Refusal rate:** how often it correctly said "not found" on the 10 unanswerable questions.

**Also report the numbers honestly**, including where it failed. A short failure analysis (three or four real examples and what you changed) is worth more than a perfect score.

## 5. Schedule (about two weeks, part-time)
| Day | Task |
|---|---|
| 1 | Download and clean the regulation text, and parse it by section |
| 2 | Chunking with metadata; embed and index |
| 3 | Basic retrieval and the FastAPI endpoint |
| 4 | Add the generation step with citations and the "not found" rule |
| 5 | Add BM25 and hybrid retrieval |
| 6 to 7 | Write the 40 questions and answer key |
| 8 | Build the evaluation script (recall@5, MRR) |
| 9 | Run all four configurations and mark faithfulness and citations |
| 10 | Failure analysis and one improvement |
| 11 | Small user test (see below) |
| 12 to 13 | README, results table, architecture diagram, cleanup |
| 14 | Publish on GitHub, and add it to your CV and LinkedIn |

## 6. Business impact test (small and honest)
Ask three or four classmates to find cited answers to 10 questions by searching the raw regulation, then with your tool. Report the **median time for each**, and state the sample size. Also report the **cost per query**, which for a local model is close to zero.

## 7. Deliverables
- A public GitHub repo with code, evaluation set and results table
- A README with the architecture, metrics, failures and limitations
- A 90-second demo video or GIF
- Two CV bullets, which I'll write once you have real numbers

## 8. Your interview story
> "At SLB I limited what the LLM could do and checked its output against the source. I then built a RAG system on pipeline regulations, and evaluated it on 40 questions: hybrid retrieval raised recall@5 from X to Y, and it correctly refused Z of 10 unanswerable questions."

That covers the topics interviewers keep raising: RAG design, evaluation and hallucination handling.

## 9. Keep applying in parallel
Send applications while you build, and describe the project as "in progress" until it's finished. I still need two answers from you to finalise your interview material: whether you wrote the comparison script at SLB, and whether you wrote the pantry check in What to Eat Today.

**One decision to make now:** do you want to use **49 CFR Part 192 (gas pipelines)** or **OSHA 29 CFR 1910 (workplace safety)** as the document set? Once you choose, I can give you the exact download steps and a starter list of 15 example questions.
