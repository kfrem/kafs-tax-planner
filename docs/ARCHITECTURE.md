# Architecture — as implemented

This documents the system **as built**, not as aspired to. The founding
design document is
[`Tax_Planner_Architecture_and_Stack_Recommendation.docx`](../Tax_Planner_Architecture_and_Stack_Recommendation.docx)
(referenced below as "the architecture doc"); section numbers cited here
(§5.2, §6.2 …) refer to it. Where the implementation deliberately
simplifies, the simplification is listed in
[DEVELOPER_HANDOVER.md](DEVELOPER_HANDOVER.md#known-simplifications).

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Language / framework | Python 3.13, Django 6.0 | single monolith, no microservices |
| Database | PostgreSQL 16 (Docker locally) | date ranges, JSONB, row-level security |
| Frontend | Django templates (server-rendered) | minimal MVP UI, no JS framework |
| PDF | WeasyPrint | advice reports rendered from the same data as the web view |
| Tests | pytest + pytest-django | 80 tests, all hand-computed expectations |

## The five components (architecture doc §4)

All five run inside one Django project (`config/`) as separate apps —
logical separation, single deployment.

### 1. Client data — `clients/`
- `Client` (per-firm, with firm's own reference code).
- `ClientFactSet` — the versioned facts JSON per client per tax year.
  Fact sets are never edited: a change creates a new row and sets
  `superseded_by` on the old one. Facts schema (see `clients/forms.py`
  `to_facts()`): `personal`, `company`, `sole_trade`, `pension`, `estate`
  sections.
- `clients/personas.py` — three canonical personas (simple / typical /
  complex) shared by the demo seed and the automated persona suite.

### 2. Rule base & calculation engine — `ruleengine/`
The five-layer knowledge model of §5.2:

- **Layer 1 (parameters)**: `TaxParameter` rows keyed like
  `income_tax.bands`, `iht.nil_rate_band`, with a PostgreSQL
  `DateRangeField` (`effective_range`) and a JSONB payload. Superseded
  rows are *closed* (upper bound set), never deleted.
- **Layer 2 (computation)**: pure functions in `ruleengine/calculators.py`
  registered via `@register(key, consumes=[...])`. `consumes` declares
  which parameter keys the calculator reads, so "what is affected if this
  rule changes?" is `calculators_consuming(key)` — a query (§5.3).
  Notable: `combined_personal_tax` computes earned income + dividends as
  one person (PA taper on total income, PA remainder to dividends,
  relief-at-source band extension).
- **Layer 3 (strategies)**: `strategy.*` calculators quantifying planning
  plays. The salary/dividend mix contains a numeric optimiser (coarse scan
  → £1 refinement) with a company-affordability constraint.
- **Layer 4 (authority)**: see `authority/` below; strategies link M2M to
  authority records.
- **Layer 5 (risk)**: `Strategy.risk_status`
  (settled/borderline/contested/untested) + `dotas_notifiable` +
  `gaar_exposure` flags, rendered prominently and unremovably in reports.

Governance objects:
- `RuleBaseRelease` — versioned releases (2024.1, 2025.1, 2025.2) with
  changelog, effective date, editor and reviewer. **Draft releases are
  invisible to the engine**: `get_parameter` only resolves rows whose
  introducing release is `released` (four-eyes enforcement in code).
- `GoldenTestCase` — 13 data-driven worked examples stored in the rule
  base itself and executed by `ruleengine/tests/test_golden_cases.py`;
  a release that breaks a golden outcome fails CI.

Engine plumbing (`ruleengine/engine.py`):
- `parameter_cache()` — request-scoped lookup cache (deliberately not
  process-lifetime: the rule base is runtime-editable).
- `parameter_provenance()` — records every parameter row resolved so the
  advice record can store exact provenance.

### 3. Authority registry & audit trail — `authority/`, `advice/`
- `Authority` — one row per statute section / SI / HMRC manual paragraph /
  tribunal decision / court judgment: canonical citation, stable URI,
  verbatim extract, and a live `status`
  (in_force/amended/superseded/overruled/doubted). Currently 20 records,
  including one court judgment (*Jones v Garnett* [2007] UKHL 35) linked
  to the salary/dividend strategy — the pattern for case-law integration.
- `AdviceRecord` (§6.2) — append-only. `save()` refuses updates,
  `delete()` refuses always. Contains: input snapshot + SHA-256 hash,
  rule-base release stamp, full results JSON (strategy, quantification,
  citations, timeframe, risk flags), **`parameters_used`** (exact
  parameter rows read: key, row id, effective-from, release), the rendered
  PDF, user and timestamp. Corrections create a new record and link
  `superseded_by`.

### 4. Advice generator — `advice/generator.py`
Pipeline per fact set: strategy eligibility (plain-Python adapters in
`advice/strategy_adapters.py`) → adapter maps facts JSON to calculator
inputs → calculator quantifies → citations/timeframe/risk attached from
the Strategy row → single immutable AdviceRecord written with provenance.
No LLM anywhere in this path (§8: deterministic engine is authoritative;
the optional LLM narrative layer is Phase 2+ and not built).

### 4b. Expert review panel — `advice/panel.py`
Four independent reviewer personas (tax accountant, tax lawyer, HMRC
consultant, business expert) deployed on demand against an advice record,
BEFORE the professional decides. Each persona is a **deterministic rule
set** (architecture doc §8: no LLM in anything that carries liability),
so a panel review is itself reproducible audit evidence:

- *Tax accountant*: independently **recomputes every figure** from the
  immutable input snapshot under the current released rules (any drift is
  a blocker), checks extraction arithmetic identities, wasted relief,
  allowance charges, provenance presence.
- *Tax lawyer*: citation presence, live authority status (overruled →
  blocker), PCRT risk-disclosure duties, DOTAS/GAAR, settlements
  legislation on spousal dividends, IHT claim deadlines and GWR.
- *HMRC consultant*: enforcement posture — LEL/NI record, dividend
  paperwork, commercial-purpose documentation, AA charge reporting,
  wholly-and-exclusively exposure, taper-cliff valuation scrutiny.
- *Business expert*: working-capital retention, pension lock-up,
  gift affordability, and pricing the NI qualifying-year trade-off in £.

`PanelReview` and `ProfessionalDecision` are append-only, firm-isolated
(RLS) tables. The decision workflow enforces the human boundary: **no
professional decision without a panel review of that record**, and
approving over a blocker requires a written override note. An LLM
narrative layer per persona is a Phase 2+ option that may only *explain*
these findings, never add or remove them.

### 5. Change monitoring — designed, not yet built
The §5.4 watchers (legislation.gov.uk API, HMRC manual change logs, Find
Case Law) are **not implemented**. The machinery they feed is: versioned
releases, effective-dated rows, draft gating, golden regression, impact
queries. A Budget change is applied today by the tax editor in Django
Admin: close the old row, add the new one under a draft release, reviewer
approves, release. This cycle was demonstrated end-to-end (see
TEST_EVIDENCE.md, "simulated Budget").

## Multi-tenancy & security — `firms/`
- `Firm`, custom `User` (role: partner/manager/staff).
- PostgreSQL **row-level security** on client/fact/advice tables, keyed to
  a session variable `app.current_firm_id` set per-request by
  `firms/middleware.py`. Enforced at the database: a connection without
  firm context cannot read or write tenant rows even from raw SQL. The dev
  database uses a non-superuser role so RLS actually applies.

## Key invariants (do not break these)
1. **Nothing in the rule base is deleted or overwritten** — rows are
   closed with an effective-to date.
2. **AdviceRecord is append-only** — corrections supersede.
3. **Every number an advice record shows is reproducible** from
   `input_data_snapshot` + `parameters_used` alone, at any future date.
4. **Draft rules never influence advice.**
5. **Every strategy result carries citation(s), timeframe, and risk
   status** — the persona suite asserts this structurally.
6. **Calculators are pure**: facts + tax year + rule base → same output,
   forever. No wall-clock, no randomness, no network.
