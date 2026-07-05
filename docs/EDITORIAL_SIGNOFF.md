# Editorial sign-off record

## Review of 5 July 2026 — full rule base (2025/26)

**Reviewing professional:** kfrem (chartered accountant; system account
`kfrem`, recorded as reviewer on rule-base releases 2024.1, 2025.1,
2025.2, 2025.3).

**Scope:** all 53 items of `RULE_BASE_REVIEW_PACK.md` as generated
5 July 2026 — 18 current-year parameters, 10 strategies, 25 authorities —
plus prior-turn verification of the IHTA 1984 citations and
*Jones v Garnett* [2007] UKHL 35. Machine pre-check: 0 failures at time
of review. Reviewer verified statutory references independently against
legislation.gov.uk and HMRC manuals (Sch 1A cross-checked to IHTM45001).

**Verdict:** YES on all 53 items. No fabricated or wrong citations
found. Three editorial corrections required and applied the same day:

| # | Finding | Correction applied |
|---|---|---|
| 1 | Spousal nil-rate-band strategy cited s.8A (ordinary NRB transfer) but not **IHTA 1984 s.8G** (RNRB transfer), leaving the combined-bands claim half-supported | s.8G added to the authority registry, cited on the strategy, and placed under watch |
| 2 | Marriage Allowance cited as ss.55B-55E, omitting the **s.55A** overview provision | Citation corrected to ITA 2007 ss.55A-55E; canonical URI repointed to s.55A |
| 3 | **TCGA 1992 s.58** described pre-F(No.2)A 2023: since 6 April 2023 no-gain/no-loss extends to separated couples (to end of third tax year after separation; unlimited under formal divorce agreement/court order) | Authority extract and strategy explanation rewritten to the current law; deeper modelling of the separation window noted as future work |

**Forward-dated changes noted by the reviewer** for future rule-base
releases (to be seeded with appropriate effective dates and re-reviewed):
- Dividend tax rate changes announced for April 2026
- BADR rate change (to 18%) from April 2026
- Savings/property income measures from April 2027
- Unused pensions brought into the IHT estate from April 2027

These are logged as monitoring targets; none affects 2025/26
computations.

**Standing arrangement:** future rule-base releases require the same
pack-based review before their status is set to released. The
`generate_review_pack` command regenerates the pack; the editorial
pre-check (`ruleengine/editorial.py`) runs in the test suite, so an
unwired rule cannot reach a reviewable state.
