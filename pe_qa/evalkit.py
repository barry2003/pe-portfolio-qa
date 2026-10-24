"""Scoring for the eval set. Retrieval scoring needs no LLM; answer scoring checks status, numbers, text and citations."""
import json
import re
from pathlib import Path


def load_questions(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def doc_of(chunk_id: str) -> str:
    return chunk_id.split("#")[0]


def numbers_in(text: str) -> list[float]:
    out = []
    for m in re.findall(r"-?\d[\d,]*\.?\d*", text):
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


def value_found(gold: float, text: str, tol: float | None) -> bool:
    t = tol if tol is not None else max(abs(gold) * 0.01, 0.01)
    return any(abs(n - gold) <= t for n in numbers_in(text))


def score_retrieval(q: dict, retrieved_chunk_ids: list[str]) -> dict | None:
    if not q["gold_docs"]:
        return None  # unanswerable or no doc requirement
    got = {doc_of(c) for c in retrieved_chunk_ids}
    gold = set(q["gold_docs"])
    return {"recall": len(gold & got) / len(gold), "hit_all": gold <= got}


def score_answer(q: dict, status: str, answer: str, citations: list[str]) -> dict:
    status_ok = status == q["gold_status"] or (q["gold_status"] == "conflict" and status == "answered" and
                                               re.search(r"restat|supersed|conflict|differ", answer, re.I) is not None)
    vals_ok = all(value_found(v, answer, q.get("tol")) for v in q["gold_values"])
    text_ok = all(any(t.lower() in answer.lower() for t in [g]) for g in q["gold_text"])
    cited_docs = {doc_of(c) for c in citations}
    cite_ok = set(q["gold_docs"]) <= cited_docs if q["gold_docs"] else True
    if q["gold_status"] == "not_found":
        correct = status == "not_found"
        cite_ok = True
    else:
        correct = status_ok and vals_ok and text_ok
    return {"status_ok": status_ok, "values_ok": vals_ok, "text_ok": text_ok, "cite_ok": cite_ok, "correct": correct}
