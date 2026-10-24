"""Generate the SYNTHETIC corpus and the eval question set from one source of truth.

Everything here is fictional. Because documents and gold answers are generated from the
same dict, the answer key cannot drift from the documents.
Run: python scripts/generate_corpus.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pe_qa.ingest import load_chunks  # noqa: E402  (resolve gold chunk ids from the corpus just written)
CORPUS = ROOT / "data" / "corpus"
EVAL = ROOT / "eval"

FUND = "Northgate Synthetic Partners Fund I"
BANNER = "SYNTHETIC DATA: fictional fund, companies and numbers created for a software demo. Not real."

# $M unless noted. TTM = trailing twelve months to 30 Sep 2026.
CO = {
    "BRIGHTWATER": dict(name="Brightwater Logistics", sector="freight brokerage / 3PL", fye="December",
        rev=84.2, ebitda=9.6, gm=14.8, net_debt=31.4, cov=4.0, hc=212, top=11.0,
        process="carrier invoice reconciliation", process_fte=3.5),
    "KEYSTONE": dict(name="Keystone Dental Supply", sector="dental supply distribution", fye="June",
        rev=47.5, ebitda=6.1, gm=31.2, net_debt=17.9, cov=3.5, hc=96, top=18.5,
        fy_rev=45.8, fy_label="FY2026 (year ended 30 Jun 2026)",
        process="customer quote preparation", process_days=4.2),
    "PINECREST": dict(name="Pinecrest HVAC Services", sector="residential HVAC services", fye="December",
        rev=38.9, ebitda=5.4, gm=38.6, net_debt=19.8, cov=3.75, hc=301, top=6.0,
        process="technician dispatch scheduling", process_fte=2.0),
    "MARLOW": dict(name="Marlow Packaging", sector="corrugated packaging manufacturing", fye="December",
        rev=62.0, ebitda=7.4, gm=22.4, net_debt=24.3, cov=4.0, hc=178, top=27.0,
        restated_ebitda=6.8, writedown=0.6, restated_gm=21.5,
        process="production scheduling and order entry", process_fte=2.5),
    "TIDELINE": dict(name="Tideline Software", sector="vertical SaaS (marina management)", fye="December",
        rev=21.3, ebitda=1.9, gm=74.0, net_debt=4.2, cov=4.5, hc=88, top=9.0,
        arr=24.8, nrr=108, churn=7.2, process="customer onboarding data migration", process_fte=1.5),
    "ORCHARD": dict(name="Orchard Foods", sector="refrigerated prepared foods", fye="September",
        rev=71.4, ebitda=8.2, gm=26.5, net_debt=29.5, cov=4.0, hc=245, top=22.0,
        process="retailer chargeback and deduction disputes", process_fte=3.0),
}
MATERIALITY_PCT = 5

def eff_ebitda(c):  # latest known EBITDA (restated where applicable)
    return c.get("restated_ebitda", c["ebitda"])

def lev(c):
    return c["net_debt"] / eff_ebitda(c)

def write(path, text):
    path.write_text(text.strip() + "\n", encoding="utf-8")

def pack(key, c):
    doc_id = f"PACK-{key}-2026-09"
    rows = [("TTM revenue ($M)", c["rev"]), ("TTM EBITDA ($M)", c["ebitda"]), ("Gross margin (%)", c["gm"]),
            ("Net debt ($M)", c["net_debt"]), ("Headcount", c["hc"]),
            ("Largest customer share of revenue (%)", c["top"])]
    if "arr" in c:
        rows += [("ARR ($M)", c["arr"]), ("Net revenue retention (%)", c["nrr"]), ("Annual logo churn (%)", c["churn"])]
    table = "\n".join(f"| {k} | {v} |" for k, v in rows)
    txt = f"""
# Monthly KPI Pack: {c['name']}
{BANNER}
Document ID: {doc_id} | Period: September 2026 | Dated: 2026-10-08 | Fiscal year end: {c['fye']}

## Headline KPIs (trailing twelve months to 30 Sep 2026, $M unless stated)
| Metric | Value |
|---|---|
{table}

## Covenant
Senior facility covenant: maximum net debt / EBITDA of {c['cov']}x, tested quarterly on trailing twelve month EBITDA. Net debt includes capital leases.

## Commentary
{c['name']} ({c['sector']}) reported September results in line with the operating plan. Management flagged no covenant concerns in this pack. Figures are management accounts and unaudited.
"""
    write(CORPUS / f"{doc_id}.md", txt)
    return doc_id

def memo(key, c):
    doc_id = f"MEMO-{key}-2026-Q3"
    date = "2026-10-14"
    proc = (f"Management estimates {c['process_fte']} full-time equivalents are consumed by {c['process']}, "
            f"a manual process that is a candidate for AI-assisted automation."
            if "process_fte" in c else
            f"Average turnaround for {c['process']} is {c['process_days']} days, driven by manual lookups across three systems; "
            f"management sees this as a candidate for AI-assisted automation.")
    extra = ""
    if key == "MARLOW":
        extra = f"""
## Restatement
Following the Q3 inventory count, Marlow recorded a ${c['writedown']}M inventory write-down. As a result, TTM EBITDA is restated from ${c['ebitda']}M (September KPI pack) to ${c['restated_ebitda']}M, and gross margin from {c['gm']}% to {c['restated_gm']}%. Revenue is unchanged. This memo supersedes the September KPI pack for these two figures.
"""
    if key == "KEYSTONE":
        extra = f"""
## Fiscal year note
Keystone's fiscal year ends 30 June. {c['fy_label']} revenue was ${c['fy_rev']}M. The $ {c['rev']}M figure in the monthly pack is trailing twelve months to 30 Sep 2026 and is not a fiscal year figure.
""".replace("$ ", "$")
    txt = f"""
# Board Memo Q3 2026: {c['name']}
{BANNER}
Document ID: {doc_id} | Dated: {date}

## Summary
{c['name']} remains on plan for the year. The largest customer represents {c['top']}% of revenue. Headcount is {c['hc']}.

## Automation and process opportunities
{proc}
{extra}
## Risks
Principal risks are customer concentration, input cost inflation, and covenant headroom under the senior facility.
"""
    write(CORPUS / f"{doc_id}.md", txt)
    return doc_id

def policy():
    doc_id = "POLICY-FUND-REPORTING"
    txt = f"""
# {FUND}: Portfolio Reporting Policy
{BANNER}
Document ID: {doc_id} | Dated: 2026-01-15

## Reporting calendar
Portfolio companies deliver a monthly KPI pack by the 10th calendar day after month end. Board memos are delivered within 15 days after quarter end.

## Definitions
Adjusted EBITDA excludes one-time items above $0.25M that are approved by the fund's finance team. Net debt means borrowings plus capital leases less unrestricted cash. Leverage means net debt divided by trailing twelve month EBITDA.

## Restatements and materiality
Any restatement of a reported headline metric by more than {MATERIALITY_PCT}% of the originally reported figure is material. Material restatements must be notified to the Investment Committee within 5 business days. When two documents conflict, the later dated document governs and the conflict must be disclosed in any summary.
"""
    write(CORPUS / f"{doc_id}.md", txt)
    return doc_id

def build_questions(ids):
    P = lambda k: f"PACK-{k}-2026-09"
    M = lambda k: f"MEMO-{k}-2026-Q3"
    by_section = {(c.doc_id, c.section.split(" (")[0]): c.chunk_id for c in load_chunks(CORPUS)}
    def ch(doc, section):  # chunk id for a document section, e.g. ch(P("MARLOW"), "Covenant")
        return by_section[(doc, section)]
    H = lambda k: ch(P(k), "Headline KPIs")
    Q = []
    # gold_chunks: the chunks holding every source fact the answer needs (the gold value itself, or the
    # inputs to the calculation; for comparisons, the inputs for every company), within gold_docs.
    def add(cat, q, status="answered", values=None, tol=None, text=None, docs=None, chunks=None):
        Q.append(dict(id=f"Q{len(Q)+1:02d}", category=cat, question=q, gold_status=status,
                      gold_values=values or [], tol=tol, gold_text=text or [], gold_docs=docs or [],
                      gold_chunks=chunks or []))
    C = CO
    add("lookup", "What was Brightwater Logistics' trailing twelve month revenue, in $M?", values=[C["BRIGHTWATER"]["rev"]], docs=[P("BRIGHTWATER")], chunks=[H("BRIGHTWATER")])
    add("lookup", "What is Tideline Software's gross margin?", values=[C["TIDELINE"]["gm"]], docs=[P("TIDELINE")], chunks=[H("TIDELINE")])
    add("lookup", "How many employees does Pinecrest HVAC Services have?", values=[C["PINECREST"]["hc"]], docs=[P("PINECREST")], chunks=[H("PINECREST")])
    add("lookup", "What share of Orchard Foods' revenue comes from its largest customer?", values=[C["ORCHARD"]["top"]], docs=[P("ORCHARD")], chunks=[H("ORCHARD")])
    add("lookup", "What is the maximum net debt to EBITDA allowed by Keystone Dental Supply's covenant?", values=[C["KEYSTONE"]["cov"]], docs=[P("KEYSTONE")], chunks=[ch(P("KEYSTONE"), "Covenant")])
    add("lookup", "What is Tideline Software's net revenue retention?", values=[C["TIDELINE"]["nrr"]], docs=[P("TIDELINE")], chunks=[H("TIDELINE")])
    add("lookup", "What is Tideline Software's ARR in $M?", values=[C["TIDELINE"]["arr"]], docs=[P("TIDELINE")], chunks=[H("TIDELINE")])
    add("lookup", "How many FTEs does Brightwater spend on carrier invoice reconciliation?", values=[C["BRIGHTWATER"]["process_fte"]], docs=[M("BRIGHTWATER")],
        chunks=[ch(M("BRIGHTWATER"), "Automation and process opportunities")])
    b = C["BRIGHTWATER"]; p = C["PINECREST"]; t = C["TIDELINE"]
    add("compute", "What is Brightwater Logistics' EBITDA margin (EBITDA divided by revenue), in percent?", values=[round(100*b["ebitda"]/b["rev"], 1)], tol=0.15, docs=[P("BRIGHTWATER")], chunks=[H("BRIGHTWATER")])
    add("compute", "What is Pinecrest HVAC Services' net debt divided by EBITDA?", values=[round(lev(p), 2)], tol=0.04, docs=[P("PINECREST")], chunks=[H("PINECREST")])
    add("compute", "How many turns of covenant headroom does Pinecrest have (covenant maximum minus actual leverage)?", values=[round(p["cov"]-lev(p), 2)], tol=0.015, docs=[P("PINECREST")],
        chunks=[H("PINECREST"), ch(P("PINECREST"), "Covenant")])
    add("compute", "What is Tideline Software's EBITDA margin in percent?", values=[round(100*t["ebitda"]/t["rev"], 1)], tol=0.15, docs=[P("TIDELINE")], chunks=[H("TIDELINE")])
    allp = [P(k) for k in CO]
    allh = [H(k) for k in CO]
    restate = ch(M("MARLOW"), "Restatement")
    add("multi-doc", "Which portfolio company has the highest net debt to EBITDA?", text=["Pinecrest"], docs=allp + [M("MARLOW")],
        chunks=allh + [restate])
    def headroom(c): return c["cov"] - lev(c)
    assert min(CO, key=lambda k: headroom(CO[k])) == "PINECREST" and max(CO, key=lambda k: lev(CO[k])) == "PINECREST"
    add("multi-doc", "Which portfolio company has the smallest covenant headroom?", text=["Pinecrest"], docs=allp + [M("MARLOW")],
        chunks=allh + [ch(P(k), "Covenant") for k in CO] + [restate])
    add("multi-doc", "Which company has the largest customer concentration, and what is the percentage?", text=["Marlow"], values=[27.0], docs=allp, chunks=allh)
    add("multi-doc", "What is the total trailing twelve month revenue across all six portfolio companies, in $M?", values=[round(sum(c["rev"] for c in CO.values()), 1)], tol=0.15, docs=allp, chunks=allh)
    m = C["MARLOW"]
    add("conflict", "What is Marlow Packaging's trailing twelve month EBITDA?", status="conflict", values=[m["restated_ebitda"]], docs=[P("MARLOW"), M("MARLOW")],
        chunks=[H("MARLOW"), restate])
    add("conflict", "What is Marlow Packaging's net debt divided by EBITDA?", status="conflict", values=[round(lev(m), 2)], tol=0.03, docs=[P("MARLOW"), M("MARLOW")],
        chunks=[H("MARLOW"), restate])
    pct = round(100*(m["ebitda"]-m["restated_ebitda"])/m["ebitda"], 1)
    add("conflict", "Does Marlow's EBITDA restatement exceed the fund's materiality threshold?", status="conflict", values=[pct], tol=0.2, text=["yes"], docs=[P("MARLOW"), M("MARLOW"), "POLICY-FUND-REPORTING"],
        chunks=[H("MARLOW"), restate, ch("POLICY-FUND-REPORTING", "Restatements and materiality")])
    k = C["KEYSTONE"]
    add("period", "What was Keystone Dental Supply's FY2026 revenue, in $M?", values=[k["fy_rev"]], docs=[M("KEYSTONE")], chunks=[ch(M("KEYSTONE"), "Fiscal year note")])
    add("period", "When does Keystone Dental Supply's fiscal year end?", text=["June"], docs=[M("KEYSTONE")], chunks=[ch(M("KEYSTONE"), "Fiscal year note")])
    add("unanswerable", "What is Tideline Software's Net Promoter Score?", status="not_found")
    add("unanswerable", "What was Keystone Dental Supply's FY2023 revenue?", status="not_found")
    add("unanswerable", "What is the compensation of Orchard Foods' CEO?", status="not_found")
    add("policy", "What percentage restatement does the fund treat as material?", values=[MATERIALITY_PCT], docs=["POLICY-FUND-REPORTING"],
        chunks=[ch("POLICY-FUND-REPORTING", "Restatements and materiality")])
    add("policy", "Who must be notified when a restatement is material, and within how many business days?", text=["Investment Committee"], values=[5], docs=["POLICY-FUND-REPORTING"],
        chunks=[ch("POLICY-FUND-REPORTING", "Restatements and materiality")])
    return Q

def main():
    CORPUS.mkdir(parents=True, exist_ok=True); EVAL.mkdir(parents=True, exist_ok=True)
    for f in CORPUS.glob("*.md"):
        f.unlink()
    ids = []
    for key, c in CO.items():
        ids += [pack(key, c), memo(key, c)]
    ids.append(policy())
    qs = build_questions(ids)
    with open(EVAL / "questions.jsonl", "w", encoding="utf-8") as fh:
        for q in qs:
            fh.write(json.dumps(q) + "\n")
    print(f"wrote {len(ids)} documents and {len(qs)} questions")

if __name__ == "__main__":
    main()
