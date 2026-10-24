# Spec: Portfolio Q&A assistant (prototype v0.1)

**Problem.** PE operating partners and finance staff spend hours pulling facts and ratios from monthly KPI packs and board memos across ~6-20 portfolio companies; numbers conflict between documents and nobody is sure which is current.

**Users.** Operating partner (asks cross-portfolio questions), finance analyst (verifies and reconciles), CFO of a portfolio company (checks how their numbers are reported).

**User stories.**
1. As an operating partner, I ask a question in plain English and get an answer with the source document so I can trust and check it.
2. As an analyst, when two documents disagree I see both values, dates and which one governs, so I do not report a stale number.
3. As a partner, when the documents do not contain the answer, the assistant says so instead of guessing.
4. As a CFO, I can see which chunk each fact came from.

**Acceptance criteria.**
- Every factual answer cites at least one retrieved chunk id; citations not in the retrieved context are flagged.
- Gold-answer accuracy on the 26-question eval set is reported by category; target at v0.1: lookup and compute at or above 90%, unanswerable 100% abstain, conflict 100% states the later value and discloses the earlier one.
- Multi-document retrieval recall at or above 0.9 (baseline 0.50).
- No answer is presented as verified unless it passes the citation check.

**Success metrics (pilot).** Time to answer a cross-portfolio question (baseline: manual lookup, to be measured); share of answers accepted by the analyst without correction; number of stale-number incidents caught.

**Out of scope for v0.1.** Real client data, write-back to any system, access control by company, audited accuracy claims.

**Risks.** Wrong answer stated confidently (mitigations: citations, abstention, eval gate); stale or conflicting documents (later-dated rule, disclosure); sensitive data leaving the environment (v0.1 is synthetic only; production needs a data-handling review).

**Build / buy / configure.** Retrieval and eval are built in-house here for transparency; a production engagement would compare managed search and hosted RAG services on cost, security review time and maintainability.
