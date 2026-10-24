import json
from pathlib import Path

from pe_qa.bm25 import BM25, tokenize
from pe_qa.evalkit import doc_of, load_questions, score_answer, score_retrieval, value_found
from pe_qa.ingest import load_chunks
from pe_qa.llm import StubLLM
from pe_qa.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"


def test_tokenize_keeps_decimals_and_drops_stopwords():
    assert tokenize("What is the 3.75x covenant?") == ["3.75", "x", "covenant"]
    assert "the" not in tokenize("the covenant")


def test_bm25_ranks_matching_doc_first():
    bm = BM25(["pinecrest covenant leverage", "marlow packaging revenue", "tideline arr"])
    s = bm.score("marlow revenue")
    assert s.index(max(s)) == 1


def test_chunks_have_stable_ids_and_header_context():
    chunks = load_chunks(CORPUS)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)) and len(chunks) > 30
    c = next(c for c in chunks if c.chunk_id.startswith("PACK-PINECREST-2026-09#headline"))
    assert "Pinecrest HVAC Services" in c.text and "301" in c.text


def test_every_gold_doc_exists():
    docs = {c.doc_id for c in load_chunks(CORPUS)}
    for q in load_questions(ROOT / "eval" / "questions.jsonl"):
        assert set(q["gold_docs"]) <= docs, q["id"]


def test_pipeline_flags_citations_outside_retrieved_context():
    stub = StubLLM(json.dumps({"status": "answered", "answer": "x 301", "citations": ["NOT-A-CHUNK#x"]}))
    a = Pipeline(str(CORPUS), stub).ask("How many employees does Pinecrest HVAC Services have?")
    assert any(f.startswith("citation_not_in_context") for f in a.flags)


def test_pipeline_parses_valid_json_and_keeps_valid_citation():
    p = Pipeline(str(CORPUS), None)
    hit = p.retrieve("How many employees does Pinecrest HVAC Services have?")[0][0].chunk_id
    p.llm = StubLLM(f'Sure: {{"status":"answered","answer":"301","citations":["{hit}"]}}')
    a = p.ask("How many employees does Pinecrest HVAC Services have?")
    assert a.status == "answered" and a.citations == [hit] and not a.flags


def test_unparseable_output_is_flagged_not_trusted():
    a = Pipeline(str(CORPUS), StubLLM("I think it is 301")).ask("Pinecrest headcount?")
    assert "unparsed_model_output" in a.flags and "uncited_answer" in a.flags


def test_value_tolerance_and_commas():
    assert value_found(3.67, "about 3.67x", 0.04) and value_found(84.2, "$84.2 million", None)
    assert not value_found(6.8, "EBITDA is $7.4M", None)


def test_score_conflict_requires_restated_value():
    q = {"gold_status": "conflict", "gold_values": [6.8], "tol": None, "gold_text": [], "gold_docs": ["A", "B"]}
    good = score_answer(q, "conflict", "Restated to $6.8M (was $7.4M)", ["A#x", "B#y"])
    bad = score_answer(q, "answered", "EBITDA is $7.4M", ["A#x"])
    assert good["correct"] and good["cite_ok"] and not bad["correct"]


def test_score_answer_requires_a_valid_citation():
    q = {"gold_status": "conflict", "gold_values": [6.8], "tol": None, "gold_text": [], "gold_docs": ["A"]}
    text = "Restated to $6.8M (was $7.4M)"
    assert not score_answer(q, "conflict", text, [], ["A#x"])["correct"]
    assert not score_answer(q, "conflict", text, ["Z#q"], ["A#x"])["correct"]
    s = score_answer(q, "conflict", text, ["A#x"], ["A#x"])
    assert s["correct"] and s["valid_cite"]


def test_score_not_found_only_passes_when_model_abstains():
    q = {"gold_status": "not_found", "gold_values": [], "tol": None, "gold_text": [], "gold_docs": []}
    assert score_answer(q, "not_found", "not in corpus", [])["correct"]
    assert not score_answer(q, "answered", "NPS is 40", [])["correct"]


def test_retrieval_score_uses_doc_level_recall():
    q = {"gold_docs": ["A", "B"]}
    assert score_retrieval(q, ["A#1", "A#2"]) == {"recall": 0.5, "hit_all": False}
    assert doc_of("A#1") == "A"


def test_chunk_level_recall_counts_exact_sections():
    q = {"gold_docs": ["A"], "gold_chunks": ["A#kpis", "A#covenant"]}
    s = score_retrieval(q, ["A#covenant", "A#risks"])
    assert s["hit_all"] and s["chunk_recall"] == 0.5 and not s["chunk_hit_all"]


def test_gold_chunks_exist_and_stay_within_gold_docs():
    ids = {c.chunk_id for c in load_chunks(CORPUS)}
    for q in load_questions(ROOT / "eval" / "questions.jsonl"):
        assert bool(q["gold_chunks"]) == bool(q["gold_docs"]), q["id"]
        assert set(q["gold_chunks"]) <= ids, q["id"]
        assert {doc_of(c) for c in q["gold_chunks"]} == set(q["gold_docs"]), q["id"]


def test_cross_portfolio_question_retrieves_packs_not_memo_boilerplate():
    hits = [c.chunk_id for c, _ in Pipeline(str(CORPUS), None).retrieve(
        "Which company has the largest customer concentration, and what is the percentage?")]
    packs = {doc_of(h) for h in hits if h.startswith("PACK-")}
    assert len(packs) == 6 and not any(h.endswith("#risks") for h in hits)
