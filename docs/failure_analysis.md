# Failure analysis: live LLM eval, k=8

Run 2026-10-24, `python -m pe_qa.cli eval --mode llm --k 8`. Model returned by the API: `claude-sonnet-5-5` on all 26 calls. No `temperature` set (removed in this run; see Caveats). Raw output: `eval/results_llm_k8.json`.

## Summary

| Category | Correct |
|---|---|
| lookup | 8/8 |
| compute | 3/4 |
| conflict | 3/3 |
| period | 2/2 |
| policy | 2/2 |
| multi-doc | 2/4 |
| unanswerable | 3/3 |
| **Total** | **23/26** (citation ok 22/26) |

Tokens in/out: 45,111 / 6,711.

Failed rows below: 3 scored incorrect (Q11, Q13, Q14) plus 2 scored correct but failing citation (Q18, Q19). Q13 and Q14 fail both.

## Failures

| ID | Question | Gold answer | Model answer (abridged) | Status (model / gold) | Retrieved chunk IDs (k=8, rank order) | Root cause |
|---|---|---|---|---|---|---|
| Q11 | How many turns of covenant headroom does Pinecrest have (covenant maximum minus actual leverage)? | 0.08x (3.75x max − 19.8/5.4 = 3.67x) | Covenant max is 3.75x, but actual net debt / TTM EBITDA is not in context, so headroom can't be computed. | not_found / answered | PACK-PINECREST-2026-09#covenant, PACK-BRIGHTWATER-2026-09#covenant, PACK-MARLOW-2026-09#covenant, PACK-ORCHARD-2026-09#covenant, PACK-TIDELINE-2026-09#covenant, PACK-KEYSTONE-2026-09#covenant, MEMO-PINECREST-2026-Q3#risks, POLICY-FUND-REPORTING#definitions | **Retrieval miss** (chunk level). `PACK-PINECREST-2026-09#headline-kpis-…` (net debt 19.8, EBITDA 5.4) is not retrieved; the five other companies' covenant chunks take its slots. Doc-level recall scores this 1.0 / hit-all, so the retrieval eval doesn't catch it. The abstention itself was correct given the context. |
| Q13 | Which portfolio company has the highest net debt to EBITDA? | Pinecrest | No company's net debt or TTM EBITDA is in context; lists covenant maximums only. | not_found / answered | POLICY-FUND-REPORTING#definitions, PACK-BRIGHTWATER-2026-09#covenant, PACK-MARLOW-2026-09#covenant, PACK-ORCHARD-2026-09#covenant, PACK-TIDELINE-2026-09#covenant, PACK-KEYSTONE-2026-09#covenant, PACK-PINECREST-2026-09#covenant, POLICY-FUND-REPORTING#reporting-calendar | **Retrieval miss.** All six packs' covenant chunks retrieved, none of their headline-KPI chunks, and `MEMO-MARLOW-2026-Q3` (restated EBITDA) missing. Abstention correct given context. Scorer marks values/text ok only because "Pinecrest" appears in the covenant list. |
| Q14 | Which portfolio company has the smallest covenant headroom? | Pinecrest | Same as Q13: covenant limits only, no actual leverage, so headroom can't be computed; notes Keystone's limit is tightest but that isn't headroom. | not_found / answered | PACK-BRIGHTWATER-2026-09#covenant, PACK-MARLOW-2026-09#covenant, PACK-ORCHARD-2026-09#covenant, PACK-TIDELINE-2026-09#covenant, PACK-KEYSTONE-2026-09#covenant, PACK-PINECREST-2026-09#covenant, POLICY-FUND-REPORTING#definitions, MEMO-BRIGHTWATER-2026-Q3#risks | **Retrieval miss.** Same pattern as Q13; needs ~13 chunks, k=8 holds 8. Abstention correct given context. |
| Q18 | What is Marlow Packaging's net debt divided by EBITDA? | conflict; 3.57x (24.3 / 6.8 restated) | Correct content: 3.57x on restated $6.8M, 3.28x on superseded $7.4M, both dates given. Output cut off mid-sentence. | answered (parse fallback; model wrote "conflict") / conflict | POLICY-FUND-REPORTING#definitions, PACK-MARLOW-2026-09#covenant, PACK-MARLOW-2026-09#headline-kpis-trailing-twelve-months-to-, MEMO-MARLOW-2026-Q3#summary, PACK-MARLOW-2026-09#commentary, MEMO-MARLOW-2026-Q3#restatement, PACK-BRIGHTWATER-2026-09#covenant, PACK-ORCHARD-2026-09#covenant | **Bad citation**, caused by output truncation: output tokens = 600 = `max_tokens`, so the JSON never closed, `parse()` fell back, and citations came back empty (flags `uncited_answer`, `unparsed_model_output`). Counted "correct" only because the raw JSON text contains "conflict". |
| Q19 | Does Marlow's EBITDA restatement exceed the fund's materiality threshold? | conflict; yes, 8.1% > 5% | Correct content: 0.6 / 7.4 = 8.1% > 5%, IC notification within 5 business days. Output cut off mid-sentence. | answered (parse fallback; model wrote "conflict") / conflict | POLICY-FUND-REPORTING#definitions, POLICY-FUND-REPORTING#restatements-and-materiality, MEMO-MARLOW-2026-Q3#restatement, MEMO-KEYSTONE-2026-Q3#fiscal-year-note, PACK-MARLOW-2026-09#covenant, POLICY-FUND-REPORTING#reporting-calendar, PACK-MARLOW-2026-09#headline-kpis-trailing-twelve-months-to-, MEMO-MARLOW-2026-Q3#summary | **Bad citation**, same truncation mechanism as Q18 (600/600 output tokens). |

Root-cause counts: retrieval miss 3, bad citation 2 (both from truncation). None from arithmetic error, wrong abstention, missed conflict, or gold set error. Q15's gold-set issue (README) didn't cause a failure here; Q15 passed.

## Observations

1. **The model abstains correctly.** In all three wrong answers the model said `not_found` and named exactly what was missing (headline KPIs). The answer failures all trace to retrieval.
2. **Doc-level recall hides the Q11 miss.** Q11 is hit-all at doc level but misses the one chunk with the numbers. A chunk-level retrieval metric would catch it.
3. **The README's "rejected alternative" paragraph doesn't match this run.** It says capping chunks per document "drops the Pinecrest headline chunk from Q10/Q11", which implies Q11 retrieves it now. At k=8 it doesn't, with or without query expansion (checked by scoring the raw question).
4. **`max_tokens=600` is too low for conflict answers**, which restate both values, both dates and the arithmetic. Truncation turns valid JSON into a parse failure.
5. **Scorer leniency.** Q18/Q19 are marked correct with status `answered` and zero citations, because `score_answer` accepts `answered` for conflict gold when the text matches `restat|supersed|conflict|differ`. Here it matched the unparsed JSON. Correct overall: 23/26; an answer that also requires `cite_ok` scores 21/26.

## Caveats

- **Not deterministic.** `temperature=0` was removed: the 2026-10-21 API version rejects sampling parameters on every model, and `anthropic` 2.3.0 no longer accepts them. Re-runs can differ. This run is a single sample.
- **Retrieved chunk IDs are recomputed.** LLM-mode results don't store them, so they come from `Pipeline.retrieve()` on the same question. BM25 is deterministic and the IDs match every citation the model returned.
- `stop_reason` isn't recorded; truncation is inferred from output tokens = 600 and the answers ending mid-sentence.
