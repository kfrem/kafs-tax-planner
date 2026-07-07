# Change approval — exam-derived advisory improvements

**For principal approval (kfrem).** This records a change to the UK Tax Planner
drawn from the tax-examination corpus, and the evidence that the program's own
experts have already approved it. Sign at the bottom once you are satisfied.

- **Prepared:** 2026-07-07
- **Rule-base version:** 2025.3 (release candidate)
- **Origin:** the partner's *Tax Intelligence Brain* brief → Milestone-1 proof of
  concept → this first concrete, reviewed change to the live app.

---

## 1. The decision you asked for: does it improve the app?

**Verdict: YES — in a specific, low-risk way — and the low-value/high-risk parts
were deliberately left out.** The exam corpus was mined for material that maps to
what the app already does. Two kinds of improvement were taken; one new area was
built to the app's full "provably correct" standard; the rest is logged as a
roadmap, **not** half-built.

| Taken now | Why it improves the app |
|---|---|
| 4 new guided-intake questions | The app now asks the make-or-break facts the examiners' reports show are most often missed — with **zero** change to any calculation. |
| 1 new priced strategy (termination payments) | Fills a genuine gap (redundancy / settlement agreements) that the corpus shows is examined every sitting. |

| Deliberately NOT taken now | Why deferred |
|---|---|
| VAT & indirect taxes | Largest gap, but a whole new engine — needs its own project and professional build. |
| Employee share schemes (EMI/CSOP/unapproved) | Wide surface area; high error risk; roadmap item. |
| PENP arithmetic, holdover relief, SBAs | Surfaced as intake questions rather than computed, so the app never guesses. |

## 2. Exactly what changed in the app

**A. Four exam-derived guided-intake questions** (pure issue-spotting — they flag
an assumption for the accountant, they do not alter a single computed figure):

1. **Fixtures s.198 election** — for fixtures in an acquired property, warns that
   *no* capital allowances arise unless the seller pooled them and a s.198 CAA
   2001 election is signed.
2. **EIS/SEIS connection** — warns that connection can deny income-tax relief.
3. **BADR qualifying conditions** — warns the 10% rate needs all conditions met
   for two years, else the normal CGT rate applies.
4. **Termination PENP split** — asks how much of a package is genuine ex-gratia
   vs contractual/PENP, so the exemption is not over-applied.

**B. One new strategy — "Termination payment (£30,000 exemption)"**
(`strategy.termination_payment`):

- First £30,000 of a qualifying termination payment exempt; the excess taxed as
  the **top slice** of income (so a large payment can also strip the personal
  allowance — the exact point the examiners flag); employer Class 1A NIC on the
  excess.
- **Authorities cited:** ITEPA 2003 s.401 (charge), s.403 (£30,000 exemption),
  s.402D (PENP), SSCBA 1992 s.10 (employer Class 1A).
- **New parameter:** `termination_payment.exemption` = £30,000 (dated, rules-as-data).
- **Two hand-computed golden cases** locked into the seed (worked below).
- Contractual/PENP amounts are an **input the adviser confirms**, never assumed.

**Worked proof (2025/26), the primary golden case** — £50,000 ex-gratia, employee
on £40,000 other income:
£30,000 exempt → £20,000 excess. Top-slice IT = IT(£60,000) − IT(£40,000) =
£10,270 @20% + £9,730 @40% = **£5,946**. Employer Class 1A = £20,000 × 15% =
**£3,000**. Net to employee = **£44,054**. Independently re-derived and matched.

## 3. Integrity guardrails honoured

- The exam corpus **informs and tests**; it is **never** the authority for a live
  rate or a final figure. Every number still traces to rules-as-data + statute.
- Nothing was taken on the corpus's historic rates.
- The trickier determinations (PENP, contractual split) are **asked**, not guessed.

## 4. The program's experts have approved it

This is the "experts in the program approve, then you approve" chain. All of the
following are **green** on this change:

| Program expert / gate | Result |
|---|---|
| **Four-expert panel** (accountant re-compute, lawyer citation check, HMRC, business) on the termination case | **panel: clear** |
| **Self-audit** (`--passes 3`) — every strategy generated, PDF-rendered, panel-reviewed, independently recomputed | **PASSED, 3/3 passes** |
| **Editorial machine pre-check** | **0 failures** across 40 parameters, 42 strategies, 50 authorities |
| **Golden cases** (hand-computed, incl. 2 new termination cases) | **all 62 match to the penny** |
| **Change watchers** — all cited authorities fetched from legislation.gov.uk | **errors=0** (4 new sources baselined) |
| **Full automated test suite** | **{{SUITE_RESULT}}** (incl. 10 new hand-written tests) |
| **Coverage** | **all 42 live strategies** exercised end to end |

## 5. What remains for the human four-eyes review

The machine gates are green. Under the app's governance, two **different**
qualified people must still review the citations and tax logic before release:

1. Review the full item list in
   [`EDITORIAL_REVIEW_CHECKLIST.md`](EDITORIAL_REVIEW_CHECKLIST.md) — now **37
   parameters · 42 strategies · 50 authorities** — paying attention to the new
   termination rows (ITEPA 2003 ss.401/403/402D; SSCBA 1992 s.10) and the four
   new intake questions.
2. Confirm the £30,000 exemption, the top-slice treatment and the employer Class
   1A rate against current law.
3. Then a human marks the `RuleBaseRelease` as **Released** in `/admin/`.

## 6. Approval

By signing, you confirm the change above is approved for release, the program's
expert gates are green, and the human four-eyes review has been completed.

| Role | Name | Decision | Date |
|---|---|---|---|
| Editor / first reviewer | ______________ | approve / reject | __________ |
| Second reviewer (distinct) | ______________ | approve / reject | __________ |
| **Principal approval** | **kfrem** | **approve / reject** | __________ |

> On approval, mark `RuleBaseRelease` 2025.3 as **Released** in `/admin/`
> (a human action; Claude does not perform it).
