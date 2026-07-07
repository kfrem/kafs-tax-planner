# UK Tax Planner — Partner Briefing

**Purpose of this document.** A self-contained overview of what the software is,
how it guarantees the numbers it produces, and exactly where an external corpus
of tax-examination questions and answers could plug in to make it stronger. It is
written for a tax professional who has *not* seen the codebase. No technical
background is assumed. If you read only one section, read **§7 — Where your Q&A
database fits**.

Prepared 7 July 2026 · Rule base version 2025.3 · Status: four-eyes editorial
review complete, ready for release.

---

## 1. What the product is (in one paragraph)

It is decision-support software for UK accounting practices. An adviser enters a
client's facts (income, dividends, property, company profits, estate, and so on)
and the system produces a written, cited tax-planning report: which strategies
apply, the pounds-and-pence effect of each, the statutory authority behind it,
and the risk level. It currently covers **41 planning strategies** across income
tax, corporation tax, capital gains tax, inheritance tax, and the four UK land
taxes (SDLT, LBTT, LTT). Think of it as a very disciplined junior tax manager
that never forgets a relief, always shows its working, and always cites the law.

## 2. The one thing that makes it different: *provable* correctness

Most tax software asks you to trust it. This one is built so that **every number
can be traced to law and independently re-derived.** The governing principle,
written into the engineering standard, is that the system must not carry "even a
scintilla of error that can affect a penny of any client." Four mechanisms
enforce that:

1. **Rules-as-data with effective dates.** Tax rates and thresholds are *not*
   hard-coded in the program. They live as dated data records (36 parameter sets
   for 2025/26). A rate that changes on 6 April is a new dated record, so the
   engine automatically uses the right figure for the right tax year and keeps
   the history. Nothing is buried in code where it can rot silently.

2. **Every strategy is pinned to a statutory authority.** Each of the 41
   strategies carries the specific Act and section it relies on (see §5). Those
   citations are fetched from legislation.gov.uk and stored *verbatim*, and a
   background watcher flags if the underlying law text changes.

3. **A four-expert review panel runs on every advice pack.** Before a report is
   trusted, four independent automated "experts" examine it: a **tax accountant**
   (re-computes every figure from scratch and fails the pack if the number
   cannot be reproduced), a **tax lawyer** (checks every claim carries a real
   citation), an **HMRC-consultant** view, and a **business** view. Each can
   raise a hard "engine defect" code that blocks release.

4. **The software audits itself.** A `self_audit` command builds real sample
   clients, generates their full advice + PDF, runs the panel, then
   *independently recomputes the answers a second time* and checks that every
   live strategy is covered. It must pass three clean times before any change is
   considered done. On top of that sits a **golden-case** test bank: worked
   examples with hand-computed answers that the build refuses to ship without
   matching.

The current build passes **287 automated tests** and a clean self-audit.

## 3. Governance — how a change becomes "released"

The rule base is **DRAFT-gated**. New or amended tax rules do not go live just
because a developer wrote them. They must pass a **four-eyes editorial review**:
two *different* qualified people independently review the complete list of every
parameter, strategy, and authority, mark each Y/N, and sign. Only when both
approve does a human mark the release as *Released* in the admin console — the
software will not do that step itself.

This is not theatre. In the most recent review cycle **both reviewers
independently caught the same two citation errors** (two non-residential SDLT
strategies had been pinned to the residential-surcharge schedule instead of the
non-residential rent schedule). They were corrected and re-verified. That is the
process working exactly as intended — and it is the kind of subtle,
easy-to-miss error where an external examiner's eye is most valuable.

## 4. Who it serves (client scenarios covered)

The system models the full range of practice clients, not just employees:

- Individuals (employment, dividends, pensions, gifts, charity)
- Owner-managed company directors (salary/dividend mix, s.455 loans, extraction)
- Sole traders and the incorporation decision
- **Landlords** — s.24 finance-cost restriction, portfolio incorporation, ADS/SDLT
- **Partnerships and LLPs** — including multi-partner profit-share allocation
- **Trusts** — relevant-property ten-year and exit charges
- Estates and IHT planning (BPR/APR, gifting, spouse/NRB, charitable 36% rate)
- Business exits (Business Asset Disposal Relief, Employee Ownership Trusts)
- Innovative companies (R&D relief, Patent Box, capital allowances/fixtures)

A **guided-intake** layer surfaces the material assumptions as questions before
advice is generated (e.g. marital status, property jurisdiction, prior trust
transfers), so the adviser confirms the facts that change the answer.

## 5. The full strategy inventory (41) with authorities

Each line is: strategy — [risk] — statutory authority relied on. "Borderline"
means the strategy carries a professional-judgement caveat in the output.

### Corporation tax
- Capital allowances / Annual Investment Allowance — [settled] — CAA 2001 s.51A
- Capital allowances on commercial-property fixtures — [settled] — CAA 2001 ss.33A–33B & s.187A
- Directors' loan s.455 charge — [settled] — CTA 2010 s.455
- Employer pension contribution — [settled] — CTA 2009 s.54
- Group relief for company losses — [settled] — CTA 2010 Part 5 (ss.97–188)
- Patent Box (10% rate) — [settled] — CTA 2010 Part 8A
- R&D tax relief (merged scheme) — [settled] — CTA 2009 Part 13 (as amended)

### Cross-cutting
- Employee Ownership Trust sale (CGT-free) — [settled] — TCGA 1992 s.236H
- Incorporation vs remaining a sole trader — [borderline] — CTA 2010 Part 3A; ITA 2007 s.35; SSCBA 1992 s.15
- Property portfolio incorporation — [borderline] — ITTOIA 2005 ss.272A–274C; TCGA 1992 s.162
- Salary/dividend extraction mix — [settled] — CTA 2010 Part 3A; ITA 2007 s.13A/s.35; *Jones v Garnett (Arctic Systems)* [2007] UKHL 35; SSCBA 1992 s.6

### Inheritance tax
- Business / Agricultural Property Relief — [settled] — IHTA 1984 ss.103–114 (BPR), ss.115–124C (APR)
- Charitable legacy and the 36% reduced rate — [settled] — IHTA 1984 Sch 1A
- Lifetime gifting: exemptions and PETs — [settled] — IHTA 1984 s.19, s.3A, s.7 & Sch 1
- Spouse exemption and transferable nil-rate bands — [settled] — IHTA 1984 s.18, s.8A, s.8D, s.8G
- Life policy in trust to fund the IHT bill — [settled] — IHTA 1984 s.5
- Pension death-benefit IHT (from April 2027) — [borderline] — IHTA 1984 s.3 (as to be amended, Finance Bill 2025–26)
- Relevant-property trust IHT charges — [settled] — IHTA 1984 ss.58–69

### Personal income tax
- Gift Aid higher-rate relief — [settled] — ITA 2007 s.414
- Bed-and-ISA — [settled] — ITTOIA 2005 s.694
- Marriage Allowance transfer — [settled] — ITA 2007 ss.55A–55E
- Partnership / LLP profit-share allocation — [borderline] — ITTOIA 2005 s.850
- Pension annual allowance carry-forward — [settled] — FA 2004 s.190 & s.228
- Personal pension contribution (relief at source) — [settled] — FA 2004 s.190
- Landlord finance-cost restriction (s.24) — [settled] — ITTOIA 2005 ss.272A–274C
- Salary sacrifice into an employer pension — [settled] — SSCBA 1992 s.6
- EIS / SEIS / VCT investment relief — [settled] — ITA 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)

### Capital gains & property taxes
- Business Asset Disposal Relief — [settled] — TCGA 1992 ss.169H–169S; ss.1H–1K
- Lettings relief (shared-occupancy let) — [settled] — TCGA 1992 s.223B; ss.222–223
- Private residence relief — [settled] — TCGA 1992 ss.222–223
- Spousal transfer before disposal — [settled] — TCGA 1992 s.58
- Timing of disposals across tax years — [settled] — TCGA 1992 ss.1H–1K
- SDLT non-residential lease (England/NI) — [settled] — FA 2003 s.55(1B) Table B; Sch 5
- SDLT non-residential purchase (England/NI) — [settled] — FA 2003 s.55(1B) Table B
- SDLT residential purchase planning (England/NI) — [settled] — FA 2003 s.55; Sch 4ZA; Sch 6ZA
- LBTT lease / non-residential / purchase (Scotland) — [settled] — LBTT(S)A 2013 s.24
- LTT lease / non-residential / purchase (Wales) — [settled] — LTTA(W) 2017 s.24

## 6. Honest limitations (so the review is grounded)

- Scope is planning strategies, not full return preparation or filing.
- Some devolved land-tax detail (e.g. Scottish ADS supplement schedules, Welsh
  higher-rate schedules) is on the next-cycle list, not yet modelled in depth.
- April-2026 changes (BPR/APR £1m cap, BADR moving to 18%) are identified and
  scheduled to be seeded with effective dates, not yet live.
- The system deliberately flags "borderline" strategies for human judgement
  rather than asserting certainty.

These are exactly the seams where an expert corpus adds the most value.

---

## 7. Where your Q&A database fits — building the "second brain"

The system today has a **rule brain**: rules-as-data plus a re-computation
engine that proves arithmetic. What it does *not* yet have is a **knowledge
brain** — a large, curated body of worked tax problems, model answers, and the
reasoning that distinguishes a good answer from a plausible-but-wrong one. A
database of tax-adviser examination questions and answers is close to the ideal
raw material for that second brain. Concretely, it could be used in five ways,
roughly in order of value:

**A. Adversarial test bank (highest value, lowest risk).**
Each exam question with a marked answer becomes an independent test the software
must pass. We feed the scenario in, generate advice, and compare against the
examiner's model answer. Every mismatch is either a real defect we fix or a
scope gap we log. This turns a static exam bank into a *living regression suite*
that continuously proves the engine against externally-authored, expert-graded
problems — a far higher bar than internally-written tests. It slots directly into
the existing golden-case and self-audit machinery.

**B. Coverage-gap finder.**
Classify every question by tax area and relief. Compare that map against our 41
strategies. Wherever the exam corpus repeatedly tests a relief we do not yet
model, that is a prioritised, evidence-backed roadmap for what to build next —
driven by what real advisers are examined on, not guesswork.

**C. Citation and reasoning cross-check.**
Exam model answers usually name the governing section and explain *why*. That is
a second, independent source to validate our authority citations against — the
same defence that caught the SDLT error, but at scale. Where the corpus cites a
case or section we don't, we investigate.

**D. Explanation quality — the narrative layer.**
The corpus shows how an examiner expects a point to be *explained*, not just
computed. It can train/shape the wording of our written advice so it reads like a
competent professional's answer: correct emphasis, the right caveats, the
"watch-points" a marker rewards. This is where "in its own league" is won — most
tools give a number; few give the reasoning a tax examiner would give marks for.

**E. Retrieval-augmented assistant (the actual "second brain").**
Index the Q&A corpus so that, when an adviser is looking at a live client, the
system can surface the closest examined precedents and model reasoning alongside
the computed answer — with a hard rule that **the corpus informs and explains but
never overrides the cited-law computation.** The rule brain stays the source of
truth for the numbers; the knowledge brain supplies context, worked analogues,
and professional framing.

**Guardrail we would insist on:** the exam corpus augments *advice and testing*;
it never becomes the arithmetic authority. Numbers always trace to
rules-as-data + statute. This keeps the integrity guarantee intact while adding
the depth and polish an examiner's knowledge base provides.

**What we would need from the partner to start (Option A first):**
- A sample of, say, 20–50 questions with their model answers and marking notes.
- The classification scheme he already uses (tax area / relief / difficulty).
- Any licensing constraints on using the material to test and to inform advice.

From a 20-question sample we can stand up a proof-of-concept adversarial test set
within the existing framework and show him, concretely, how his material makes
the software measurably harder to fool.

---

*This briefing is a plain-English summary. The full engineering detail lives in
`docs/ARCHITECTURE.md`, `docs/ENGINEERING_PLAYBOOK.md`, the strategy coverage map
in `docs/TAX_PLANNING_COVERAGE.md`, and the signed review pack in
`docs/RULE_BASE_REVIEW_PACK.md`.*
