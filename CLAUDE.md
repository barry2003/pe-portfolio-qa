# pe-portfolio-qa

Prototype: question answering over synthetic PE portfolio documents (monthly packs, IC memos, policy) with citations.

## Layout
- `pe_qa/`: ingest.py (section chunking), bm25.py (dependency-free BM25), llm.py (Anthropic client + StubLLM), pipeline.py (retrieve, prompt, parse, citation validation), evalkit.py, cli.py
- `scripts/generate_corpus.py`: deterministic corpus + eval questions from one source of truth
- `data/corpus/` (13 docs), `eval/questions.jsonl` (26 questions), `tests/`

## Commands
- `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- `pytest`
- `python -m pe_qa.cli eval --mode retrieval --k 8`
- `python -m pe_qa.cli eval --mode llm` (needs ANTHROPIC_API_KEY in .env)

## Rules
- Never commit `.env` or keys.
- Answers must be status answered|not_found|conflict with citations that exist in retrieved context.
- Record before/after eval numbers for any retrieval change.
- Known failure: multi-doc questions Q13, Q14 (k=8 can't hold every pack's headline + covenant chunks plus the restatement memo); Q15 passes. Live-model accuracy: 23/26 as scored, 23/26 with citations required (one sample, max_tokens=1200).
- Show diffs before committing; the owner makes the commits.
