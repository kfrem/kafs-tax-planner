# Scope: landlord & property planning + guided (adaptive) fact intake

A build-ready specification for the next developer. Two related
workstreams:

- **A. Landlord & property planning** — answer the questions UK landlords
  actually ask: hold personally vs in a company vs in trust, sell vs hold,
  and how to structure a portfolio to minimise tax.
- **B. Guided adaptive intake** — make the app *ask the follow-up questions*
  it needs (married? spouse's income? mortgaged? hours spent managing?) so
  the advice is built on real facts, never silent assumptions.

Follow the existing conventions throughout: read
[`ENGINEERING_PLAYBOOK.md`](ENGINEERING_PLAYBOOK.md) and
[`ONBOARDING.md`](ONBOARDING.md) §5 first. Every new rule is **data**, every
calculator is **hand-computed and golden-tested**, and — because this is
high-liability territory — **nothing ships to a real client until the tax
editor has reviewed it against the primary source** (four-eyes, §5.6). This
document tells you *what* to build; the exact figures and the wording of
every recommendation are the tax editor's to confirm.

Status: scoped, not started. Last updated 6 July 2026.

---

## Why this matters (the business case)

UK landlords are a huge, tax-anxious, willing-to-pay market, and
"should I incorporate my portfolio?" is a question accountants get
constantly and struggle to model by hand. No US tool (Corvee, TaxPlanIQ)
touches UK property; UK compliance tools don't do planning. If the app
answers this well and defensibly, it becomes the flagship reason a firm
subscribes. See [`PRICING.md`](PRICING.md) and
[`HOSTING_AND_COSTS.md`](HOSTING_AND_COSTS.md) for the commercial context.

---

# Workstream A — Landlord & property planning

## A0. The decisions to support

1. **Hold personally vs in a limited company** (incorporate the portfolio).
2. **Sell vs hold** (CGT now vs keep letting vs hold to death).
3. **Ownership split with a spouse** (income + CGT band/allowance planning).
4. **Trust** (advanced — Phase 2 of this workstream).

## A1. Rental income tax, including Section 24 (the foundation)

Nothing else works until the app models a landlord's *income tax on rents*
properly. Today it treats rent as generic "other income" — that is not good
enough for planning.

Model (verify every figure/rule against the primary source and cite it):

- **Rental profit** = rents − allowable expenses − capital allowances
  (commercial / furnished holiday lets only).
- **Section 24 finance-cost restriction** (the crux): for an *individual*
  holding *residential* lettings, mortgage interest is **not** deducted from
  profit; instead a basic-rate (20%) tax reducer applies. Higher-rate
  landlords therefore overpay vs a company. *Commercial* property and
  *furnished holiday lets* are **exempt** from Section 24 (interest fully
  deductible). Primary sources to cite: ITTOIA 2005 s.272A (disallowance),
  ITA 2007 s.274A–274C (the reducer). Introduced by F(No.2)A 2015 s.24.
- Interacts with the **personal allowance taper** and the existing
  `combined_personal_tax` — rental profit is non-savings income and stacks
  with other income.

New parameter(s): a `property.income_tax` payload capturing the Section 24
reducer rate and the property allowance. New calculator:
`property_rental_income_tax(facts, tax_year)` returning the tax with and
without Section 24 so the *cost* of personal ownership is explicit.

## A2. Company ownership (the comparison)

- Company pays **corporation tax** on rental profit with finance costs
  **fully deductible** (no Section 24) — reuse the existing
  `corporation_tax` calculator.
- **Extraction**: getting cash out is taxed personally — reuse
  `combined_personal_tax` / `salary_dividend_mix`.
- **ATED** (Annual Tax on Enveloped Dwellings): an annual charge on a
  company holding a *residential* dwelling worth > £500k, **unless a relief
  applies** (commercial letting to unconnected tenants is the common one).
  Banded by property value. Primary source: FA 2013 Part 3. New parameter:
  `ated.bands`. Most buy-to-let companies letting to third parties will
  claim relief — model the relief and flag when ATED bites (e.g. a director
  living in a company property).

Deliverable: `strategy.property_hold_personal_vs_company` — a like-for-like
net-cash comparison over a chosen holding period.

## A3. The cost of incorporating (this is where it's easy to be wrong)

Moving existing properties into a company is a disposal at market value and
usually triggers **two upfront taxes** that can dwarf the annual saving:

- **CGT on transfer** — market-value disposal for the individual, **unless
  incorporation relief (TCGA 1992 s.162)** applies. s.162 is available only
  where the letting is run as a genuine *business* (active, significant
  time — the *Ramsay v HMRC* [2013] UKUT benchmark, ~20 hrs/week is often
  cited), rolling the gain into the share base cost. Model both: with and
  without s.162.
- **SDLT/LBTT/LTT on transfer** — the company acquires at market value, so
  land tax is due (including the residential additional-dwelling surcharge,
  and note the **15% flat SDLT** on corporate residential > £500k, FA 2003
  Sch 4A, subject to reliefs). **Partnership incorporation relief** (FA 2003
  Sch 15, esp. para 18) can reduce/eliminate SDLT where a *genuine
  partnership* incorporates — highly technical, HMRC-scrutinised. Model the
  charge; flag partnership relief as an adviser judgement, not an automatic.

Deliverable: extend A2 to compute the **break-even** — how many years of
Section 24 / CT savings it takes to recoup the CGT + SDLT transfer cost.
That break-even *is* the advice. **Tax-editor sign-off is mandatory here**;
s.162 eligibility and SDLT partnership relief are exactly where wrong logic
becomes negligent advice.

## A4. Spousal / joint ownership

Transfer a share to a spouse on a no-gain/no-loss basis (TCGA 1992 s.58,
already modelled) to use their lower rate band and CGT allowance for both
rental income and eventual disposal. Note **Form 17** where beneficial
ownership is unequal. Deliverable: `strategy.property_spousal_ownership_split`
(reuses much of the existing spousal-transfer CGT work).

## A5. Sell vs hold

Compose the existing pieces: CGT on sale now (built) vs continue letting
(A1 income tax) vs hold to death (CGT uplift on death + the existing IHT
module). Deliverable: `strategy.property_sell_vs_hold` — a multi-year,
multi-outcome comparison. Depends on a simple multi-year projection helper.

## A6. Portfolio aggregation

Today the engine models a single disposal / single estate. Landlords have
*portfolios* (e.g. 5 residential + 1 commercial, some mortgaged). Add a
`property.portfolio` fact shape (a list of properties: type, value, base
cost, mortgage, rent, expenses) and let A1–A5 operate on the aggregate.

## A7. Trusts (Phase 2 of this workstream — flag, don't build yet)

Settling property into trust: CGT on transfer (holdover s.165/s.260 may
apply), and the IHT **relevant property regime** (entry charge over the NRB,
10-yearly principal charges, exit charges — IHTA 1984). This is a large,
specialist build. Scope it separately when A1–A6 are proven.

---

# Workstream B — Guided adaptive fact intake

**The requirement (in the founder's words):** the app must *ask follow-up
questions* so the planning is correct — e.g. once basic data is entered, ask
whether the client is married, whether the spouse works, the spouse's
income, whether properties are mortgaged, how many hours the client spends
managing them. Without this, the app silently assumes (single, no spouse
income, no mortgage) and the advice is wrong.

## B1. Questions as data (not hard-coded forms)

Mirror the "rules are data" principle. Define a **question set** as data —
each question a row/record with:

- `id`, `prompt` (plain English), `answer_type` (yes/no, number, money,
  choice), the **`fills` fact path** it populates (e.g. `personal.spouse_income`),
  and a **`condition`** — when to ask it (e.g. ask spouse income only if
  `personal.married == true`).

Conditions make it *adaptive*: answering "married: yes" reveals the spouse
questions; "has residential lettings with a mortgage: yes" reveals the
interest-amount question (needed for Section 24); "considering a company:
yes" reveals the hours-managed question (needed for the s.162 business test).

## B2. Completeness gate before advice

The advice generator should, before running a strategy, check that the facts
that would *change the outcome* are present. If a relevant fact is missing,
surface the question rather than assuming a default. Tie this to the
existing adapter/eligibility layer: an adapter already knows which facts it
reads — extend that so it can declare which facts are *decision-critical*
and must be answered, vs optional.

## B3. Surface every assumption (the safety net)

Even with good questions, some facts get defaulted. Every generated
`AdviceRecord` should **list the assumptions it made** ("assumed the spouse
has no other income"; "assumed the property has always been residential
let") so the accountant can catch a wrong one before it reaches the client.
This is cheap to add, hugely reduces the "it assumed something wrong" risk
the founder raised, and strengthens the defensibility story.

## B4. UI

A guided wizard / progressive form (HTMX fits the stack) that walks the
questions in order, showing conditional ones as answers come in. Not a wall
of fields. Keep it staff-facing (the accountant fills it, often with the
client on a call).

---

## Suggested build order (milestones)

1. **B1–B3 questionnaire engine** (questions-as-data + completeness gate +
   assumptions list). Valuable on its own — it improves *every* existing
   strategy immediately, including the married/spouse example.
2. **A1 rental income tax + Section 24.** The foundation; also a strong demo
   on its own ("here's the Section 24 hit you're taking").
3. **A2 + A3 personal-vs-company with the incorporation cost & break-even.**
   The flagship. Requires the most tax-editor involvement.
4. **A4 spousal split** and **A6 portfolio aggregation** (they reinforce each
   other).
5. **A5 sell-vs-hold** (needs a small multi-year projection helper).
6. **A7 trusts** and **B4 polished wizard UI** — later.

## Definition of done (every item, no exceptions)

Per the playbook: implementation · hand-computed tests (with the working
shown) · golden case(s) in the seed · authorities added/cited · invariants
still green · docs + defect log updated · CI green · **and tax-editor
sign-off recorded in `EDITORIAL_SIGNOFF.md` before any real-client use.**

## Authorities to add to the registry (research + cite these)

Section 24 — ITTOIA 2005 s.272A, ITA 2007 s.274A–274C; incorporation relief —
TCGA 1992 s.162; holdover — TCGA 1992 s.165 / s.260; SDLT on corporate
residential & partnership relief — FA 2003 Sch 4A and Sch 15; ATED — FA 2013
Part 3; the property-business-as-business test — *Ramsay v HMRC* [2013] UKUT
0226; the relevant-property trust regime — IHTA 1984 Part III Ch III.

## Milestone 1 — task breakdown (guided intake engine)

Start here. This slice is self-contained, improves **every** existing
strategy, and demos the founder's exact example (married? spouse income?).
Each task is one commit-sized piece; follow the six-part definition of done.
Recommended order:

**Task 1 — Fact-path helpers.** New `advice/facts.py`: `get_fact(facts,
"personal.spouse_income", default=None)` and `set_fact(facts, path, value)`
that read/write the nested `ClientFactSet.facts` JSON by dotted path. Pure,
no DB. *Tests:* nested get/set, missing intermediate keys, overwrite.

**Task 2 — Questions as data.** New `advice/intake.py` with a `Question`
dataclass — `id`, `prompt`, `answer_type` ('bool' | 'money' | 'number' |
'choice'), `fills` (dotted fact path), `condition` (a `Callable[[dict],
bool]` deciding *when to ask*), `required` (decision-critical or optional),
`help_text` — and a `QUESTIONS` list. Seed the first set to prove
conditionals: `married?` → if true reveal `spouse_income`, `spouse_works?`;
`owns_rental_property?` → if true reveal `property_is_mortgaged?` → if true
reveal `annual_mortgage_interest`. Keep it plain Python, like
`strategy_adapters.py` (explicit and auditable, not a DSL). *Tests:* every
question well-formed; `fills` paths are unique.

**Task 3 — The intake engine.** In `advice/intake.py`:
`applicable_questions(facts)` (condition true), `outstanding_questions(facts)`
(applicable **and** the `fills` path is still empty), and
`missing_required(facts)` (outstanding + `required`). *Tests (hand-reasoned):*
a single client shows no spouse questions; setting `personal.married=True`
makes `spouse_income`/`spouse_works` outstanding; answering `spouse_income`
drops it from outstanding; a mortgage question only appears once
`owns_rental_property` and `property_is_mortgaged` are true.

**Task 4 — Assumptions on advice (B3).** Migration adding
`assumptions = JSONField(default=list)` to `AdviceRecord` (keep the
append-only `save()` working — assumptions are set at creation, never
updated). In `advice/generator.py`, when a strategy runs while a
decision-critical fact is defaulted, append a plain-English line
("Assumed the spouse has no other income"). Surface the list in the advice
detail template and the PDF. *Tests:* generating with no spouse data records
the assumption; the record is still undeletable/immutable; a fully-answered
client records no assumption.

**Task 5 — Completeness surfacing (B2).** Expose `outstanding_questions()`
on the client/advice views so unanswered decision-critical questions are
shown prominently before/at generation. **Policy:** do **not** block
generation — generate with the assumptions list (Task 4) as the safety net,
and nudge the user to answer. *Tests:* a view test that an unanswered
critical question is surfaced.

**Task 6 — Guided wizard UI (HTMX).** A staff-facing view (e.g.
`clients/<id>/intake`) that renders the next outstanding question, POSTs the
answer via `set_fact` into the `ClientFactSet`, and re-renders the next —
one question at a time, conditionals appearing as answers come in. *Tests:*
GET shows a question; POST saves the fact and advances; access is
firm-scoped (a firm user cannot answer another firm's client).

**Task 7 — Confirm facts flow into advice.** Verify the seeded questions
fill facts that real strategies consume (Marriage Allowance and the CGT
spousal strategies already read `personal.spouse_income`), so answering them
visibly changes the advice and the assumptions. Keep the personas green
(they set these facts explicitly, so unaffected).

**Task 8 — Docs.** Update `TEST_EVIDENCE.md` (new test files), note the
"how to add a question" pattern in `ONBOARDING.md` §5, and tick this
milestone in `DEVELOPER_HANDOVER.md` §6 item 0.

**Milestone-1 done when:** a staff user opens a client, is asked the
adaptive follow-up questions (married → spouse income, etc.), answers them,
generates advice that reflects those answers, and any unanswered
decision-critical fact appears as a stated assumption on the advice — all
under the usual green suite + CI. No property tax maths yet; that is
Workstream A, which builds on this.

## Open questions for the founder / tax editor

- Which nations' property rules first — England (SDLT) only, or all three
  from the start? (Land-tax engines for all three already exist.)
- How aggressive on partnership SDLT relief and s.162 — model them, or model
  the charge and leave the relief as an adviser flag? (Recommend the latter
  until reviewed — over-claiming relief is the dangerous direction.)
- Furnished holiday lets: in or out of the first cut? (Their rules changed
  from April 2025 — verify current position before modelling.)
