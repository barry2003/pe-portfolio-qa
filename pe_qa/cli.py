"""CLI: python -m pe_qa.cli ask "question" | eval --mode retrieval|llm"""
import argparse
import json
import statistics
from pathlib import Path

from .evalkit import load_questions, score_answer, score_retrieval
from .pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
QUESTIONS = ROOT / "eval" / "questions.jsonl"


def cmd_ask(args):
    from .llm import AnthropicLLM
    p = Pipeline(str(CORPUS), AnthropicLLM(), k=args.k)
    a = p.ask(args.question)
    print(json.dumps(a.__dict__, indent=2))


def cmd_eval(args):
    qs = load_questions(QUESTIONS)
    p = Pipeline(str(CORPUS), None, k=args.k)
    rows = []
    if args.mode == "llm":
        from .llm import AnthropicLLM
        p.llm = AnthropicLLM()
    for q in qs:
        row = {"id": q["id"], "category": q["category"], "question": q["question"]}
        if args.mode == "retrieval":
            hits = [c.chunk_id for c, _ in p.retrieve(q["question"])]
            row["retrieval"] = score_retrieval(q, hits)
            row["retrieved"] = hits
        else:
            a = p.ask(q["question"])
            row["retrieval"] = score_retrieval(q, a.retrieved)
            row["answer"] = a.answer
            row["status"] = a.status
            row["citations"] = a.citations
            row["flags"] = a.flags
            row["score"] = score_answer(q, a.status, a.answer, a.citations, a.retrieved)
            row["tokens"] = [a.input_tokens, a.output_tokens]
            row["model"] = a.model
        rows.append(row)
    out = ROOT / "eval" / f"results_{args.mode}_k{args.k}.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print_summary(rows, args.mode, args.k, out)


def print_summary(rows, mode, k, out):
    cats = sorted({r["category"] for r in rows})
    print(f"mode={mode} k={k} questions={len(rows)}  -> {out.name}")
    ret = [r for r in rows if r["retrieval"]]
    print(f"retrieval (answerable, {len(ret)} q): mean doc recall={statistics.mean(r['retrieval']['recall'] for r in ret):.2f}, "
          f"hit-all={sum(r['retrieval']['hit_all'] for r in ret)}/{len(ret)} | "
          f"chunk recall={statistics.mean(r['retrieval']['chunk_recall'] for r in ret):.2f}, "
          f"hit-all={sum(r['retrieval']['chunk_hit_all'] for r in ret)}/{len(ret)}")
    for c in cats:
        rr = [r for r in ret if r["category"] == c]
        if rr:
            print(f"  {c:12s} doc recall={statistics.mean(r['retrieval']['recall'] for r in rr):.2f} hit-all={sum(r['retrieval']['hit_all'] for r in rr)}/{len(rr)}"
                  f" | chunk recall={statistics.mean(r['retrieval']['chunk_recall'] for r in rr):.2f} hit-all={sum(r['retrieval']['chunk_hit_all'] for r in rr)}/{len(rr)}")
    if mode == "llm":
        ok = sum(r["score"]["correct"] for r in rows)
        cite = sum(r["score"]["cite_ok"] for r in rows)
        print(f"answers correct: {ok}/{len(rows)}   citation ok: {cite}/{len(rows)}")
        for c in cats:
            rr = [r for r in rows if r["category"] == c]
            print(f"  {c:12s} {sum(r['score']['correct'] for r in rr)}/{len(rr)}")
        print("tokens in/out:", sum(r["tokens"][0] for r in rows), sum(r["tokens"][1] for r in rows))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--k", type=int, default=8); a.set_defaults(fn=cmd_ask)
    e = sub.add_parser("eval"); e.add_argument("--mode", choices=["retrieval", "llm"], default="retrieval")
    e.add_argument("--k", type=int, default=8); e.set_defaults(fn=cmd_eval)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
