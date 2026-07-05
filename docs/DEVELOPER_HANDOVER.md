# Developer handover

Everything a developer taking over needs: what was built and in what
order, how to stand the system up from nothing, how to verify you get the
same results the original build got, what is deliberately simplified, what
went wrong and how it was fixed, and what remains.

Companion documents: [ARCHITECTURE.md](ARCHITECTURE.md) (system as built),
[TEST_EVIDENCE.md](TEST_EVIDENCE.md) (test inventory and results).

---

## 1. Build log (chronological)

Built July 2026 in a single continuous engagement, PostgreSQL-first, tests
green at every checkpoint. Test count shows cumulative growth.

| # | Work | Evidence / outcome |
|---|---|---|
| 1 | Django project scaffold: `config` + apps `firms`, `authority`, `ruleengine`, `clients`, `advice`, `reports` | project boots |
| 2 | PostgreSQL 16 in Docker; **non-superuser app role** so RLS is real | README "Getting started" |
| 3 | Firms, roles, RLS policies + per-request firm context middleware | `firms/tests.py` (cross-tenant denial) |
| 4 | Authority registry with status lifecycle | `authority/models.py` |
| 5 | Rule engine models: `TaxParameter` (date-ranged), `Strategy`, `RuleBaseRelease`, `GoldenTestCase` | `ruleengine/models.py` |
| 6 | Deterministic calculators + registry with `consumes` declarations | `ruleengine/engine.py`, `calculators.py` |
| 7 | Seed: real 2024/25 + 2025/26 parameters, 20 authorities, 7 strategies, 13 golden cases | `seed_rule_base` command |
| 8 | Client data module, versioned fact sets, CSV import | `clients/` |
| 9 | Advice generator + append-only `AdviceRecord` | `advice/` |
| 10 | WeasyPrint branded PDF reports | `reports/` |
| 11 | Minimal server-rendered UI (login, clients, facts entry, advice, PDF download) | `templates/` |
| 12–13 | Golden regression suite; full suite green | 29 tests |
| 14–16 | `combined_personal_tax`: whole-income interaction (PA taper incl. dividends, PA remainder to dividends); strategies report *incremental* tax over other income. **Changed Sarah's recommendation materially** — see §4 defect/finding log | 37 tests |
| 17–18 | Pension: relief-at-source band extension + ANI reduction; relevant-UK-earnings cap (FA 2004 s.190); employer-contribution route with CT saving | 43 tests |
| 19 | Salary optimiser (scan to £1) + request-scoped parameter cache; found & fixed affordability bug | 46 tests |
| 20 | IHT module: 4 parameters, estate calculator, 3 strategies, 7 IHTA authorities, release 2025.2 | 58 tests |
| 21 | Audit integrity: draft-release gating in `get_parameter`; `parameters_used` provenance on every advice record; provenance table in the PDF | 63 tests |
| 22 | Personas Emma (simple) / Sarah (typical) / Victor (complex) as permanent consistency suite; *Jones v Garnett* added to authority registry | 80 tests |
| 23 | Layered documentation (this file, ARCHITECTURE.md, TEST_EVIDENCE.md) | — |
| 24 | **Expert review panel**: four deterministic reviewer personas, per-persona + overall verdicts, append-only `PanelReview`/`ProfessionalDecision` with RLS, decision gating (panel-first, blocker override notes), UI deploy button, provenance-style independent recomputation check | 92 tests |
| 25 | git repository + GitHub Actions CI (Postgres service container, non-superuser role, full suite on every push/PR): https://github.com/kfrem/kafs-tax-planner | CI green |
| 26 | Accountant-grade presentation: `quant_table` template filter (£/percent/Yes-No formatting, humanised labels, nested + columned tables) used by both the PDF and the web view | 96 tests |
| 27 | **Property/CGT module**: CGT (AEA, band-straddling rates) and SDLT (bands, 5% surcharge, FTB relief) calculators; PPR relief with final-9-months rule, spousal transfer before disposal, SDLT purchase planning strategies; release 2025.3, 5 TCGA/FA 2003 authorities, 3 golden cases; Victor persona extended with a rental disposal | 109 tests |
| 28 | **Change-monitoring pipeline v1** (§5.4): `monitoring` app — WatchedSource per authority URI, diff watchers with pluggable fetchers and markup normalisation, ChangeAlert editorial queue (notes + release requirements), staff-only queue UI, `seed_watched_sources`/`run_watchers` commands. Live-baselined against all 25 real primary sources; the first run caught a wrong case-law URI (fixed to BAILII) | 119 tests |
| 29 | **Containerised**: production Dockerfile (python:3.13-slim + Pango for WeasyPrint, gunicorn, WhiteNoise, non-root user), docker-compose stack that provisions the non-superuser DB role automatically, CI `docker-image` job building the image on every push, docs/DEPLOYMENT.md with the UK hosting comparison | 119 tests + image build in CI |
| 30 | **Engineering playbook + zero-cost hardening**: docs/ENGINEERING_PLAYBOOK.md (shareable standards for any AI-assisted accounting build); ruff lint (10 findings fixed) and pip-audit (0 known CVEs) added as a CI `lint` job; `manage.py check --deploy` in the test job | 119 tests, 3 CI jobs |
| 31 | **Section A batch** (executed autonomously): employment-income field wired through every adapter (relevant-UK-earnings distinction preserved); feed-specific watchers (legislation.gov.uk XML API, gov.uk content API, per-type resolver, `run_watchers --rebaseline`); authority status workflow UI with append-only `AuthorityStatusChange` log feeding the editorial queue; per-firm `AdviceImpactAlert`s (effective-date-scoped, idempotent, RLS) with review UI + `generate_impact_alerts` command; scenario modelling (ephemeral, same engine path, side-by-side deltas); TOTP MFA (django-otp, QR enrolment, middleware enforcement) and per-client `ClientAccess` grants enforced across every client-touching view; `AdviceNarrative` layer with the §8 validator (fabricated numbers/citations rejected before storage; deterministic drafter now, LLM pluggable through the same gate); explain-only panel persona voices. Local dev DB rebuilt on portable PostgreSQL 16.9 (Docker Desktop unrecoverable without interactive session) | **162 tests** |

## 2. Standing it up from nothing

Follow README "Getting started" verbatim. Summary:

```bash
# 1. PostgreSQL 16 with a NON-superuser app role (RLS depends on this)
docker run -d --name taxplanner-pg -e POSTGRES_DB=taxplanner \
  -e POSTGRES_USER=taxplanner -e POSTGRES_PASSWORD=taxplanner_dev_pw \
  -p 5432:5432 postgres:16
# then create app_user per README (§Getting started)

# 2. Python env
python -m venv venv && source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt                        # WeasyPrint needs GTK3 on Windows

# 3. Database + data
python manage.py migrate
python manage.py seed_rule_base --release   # DRAFT by default; --release is dev-only
python manage.py seed_demo_clients          # Emma / Sarah / Victor + advice + PDFs

# 4. Verify you reproduce the original results
python -m pytest -q          # expect: 162 passed
python manage.py runserver   # log in: demo / demo-pass-123
```

**The reproduction check is the point**: if `pytest` shows 162 passing you
have byte-for-byte the same calculation behaviour this build had — every
expectation in the suite is a hand-computed number, not a snapshot.

## 3. Conventions you must keep

1. **Hand-compute every test expectation.** Never assert what the code
   returns; assert what the legislation says, worked by hand (or from an
   HMRC published example), with the working shown in the test comment.
2. **Rules are data.** A Budget change is parameter rows under a new
   release — if you find yourself editing a calculator for a rate change,
   stop; the design is wrong or you are.
3. **Close rows, never delete.** Effective ranges are the audit trail.
4. **New strategy = calculator + adapter + Strategy row + authorities +
   golden case + hand-computed tests.** All six, no exceptions.
5. **Additions to personas** need corresponding expectations in
   `advice/tests/test_personas.py`; changing persona facts requires
   re-deriving the pinned numbers.
6. **Seed is idempotent** — `update_or_create`/delete-and-recreate per
   row; keep it that way, it's how dev/test/demo environments converge.
7. Releases created by the seed are DRAFT by default; `--release` exists
   for dev/tests only. In any real deployment the reviewer flips status in
   Admin (four-eyes, §5.6).

## 4. Defect & finding log (what went wrong, honestly)

| ID | Found | What happened | Fix / regression guard |
|---|---|---|---|
| F1 | Persona walkthrough | Strategies quantified each income in isolation: Sarah's £28k sole trade was invisible to the salary/dividend optimiser, overstating net by ~£10k/yr and recommending the wrong salary | `combined_personal_tax` + incremental-tax reporting; `test_income_interaction.py` pins her exact numbers |
| F2 | Optimiser build | First scan recommended £95,000 salary out of £95,000 profit — employer NIC (~£13.5k) funded from thin air. The old fixed grid had masked it | Affordability constraint (salary + employer NIC ≤ profit); `test_respects_company_affordability` pins the boundary (£9,347 max from £10,000) |
| F3 | Simulated-Budget demo | Advice record stamped release 2025.2 while computing from another release's parameter rows; also, rows under a *draft* release would have influenced calculations | Draft gating in `get_parameter` + `parameters_used` provenance on every record; `test_provenance.py` |
| F4 | Test authoring (twice) | My own hand-computed expectations were wrong (incorporation higher-rate figure; Victor's charity baseline ignoring his existing £50k legacy). The engine was right both times | Corrected with working shown in comments. Process lesson: derive, don't eyeball |
| F5 | Cleanup attempt | Tried to delete a simulation advice record; the model refused (`AdviceRecord cannot be deleted`) | Not a defect — evidence the audit trail resists even developers. Superseded instead, as designed |
| F6 | Section A batch, CI run | New view tests passed locally (DEBUG=true) but 301'd in CI (DEBUG=false enables SECURE_SSL_REDIRECT; the test client speaks plain HTTP) — an environment-parity gap, not a code bug | Autouse conftest fixture pins SECURE_SSL_REDIRECT off in tests; suite re-run locally under DEBUG=false before pushing. Lesson: reproduce CI's environment locally when CI disagrees |
| F7 | Editorial-queue view tests | My own test asserted the authorities page would contain the strategy *code* (`salary-dividend-mix`); the template renders the strategy *name* (`Salary/dividend extraction mix`). The view was right | Assertion corrected to the displayed name, with a comment noting the template lists by name. Same F4 lesson: assert what the rendered artefact actually contains, don't eyeball it |

## 5. Known simplifications (each needs tax-editor review, §5.6)

Personal tax:
- Standard allocation order only; no beneficial-ordering optimisation of
  the personal allowance between income types.
- Dividend allowance modelled as relief at the lowest dividend slice, not
  as a band-consuming nil-rate band.
- `personal.other_income` is treated as non-dividend, non-savings income;
  there is no separate PAYE-employment field yet (affects relevant UK
  earnings, which conservatively counts only own-company salary +
  sole-trade profit).
- No Scottish/Welsh rate variants (parameter model supports them as
  variant rows when needed).

Pension:
- Threshold/adjusted income are entered facts, not derived; MPAA not
  modelled; the annual-allowance excess is reported as a charge *basis*,
  not converted to a charge at marginal rate.

Property / CGT:
- Business Asset Disposal Relief: qualifying gains *above* the £1m
  lifetime limit are charged at the standard higher non-residential rate
  (24% in 2025/26), not band-split — correct whenever qualifying gains
  reach the basic-rate band (the normal case) and conservative otherwise;
  the annual exempt amount is set against the relieved gain (conservative
  where an unrelieved excess exists); the qualifying conditions
  (two-year ownership, 5% personal-company holding for shares) are assumed
  met, being a matter for the adviser. No composition yet with a
  concurrent non-BADR disposal in the same year.

IHT:
- No BPR/APR, settled property, foreign assets, GWR detection, or
  s.38 grossing-up; 36% baseline is (net estate − spouse − NRB) without
  the full Sch 1A component split; first death assumed fully
  spouse-exempt in the spousal strategy.

Cross-cutting:
- Incorporation comparison does not compose with the *recommended* (as
  opposed to recorded) extraction from the main company.
- CSV import is minimal; UI is developer-grade, not product-grade.

## 6. Remaining work (ordered)

Done since first draft of this list: git + GitHub Actions CI, accountant-
grade presentation, property/CGT module, **change-monitoring watchers**
(§5.4: legislation.gov.uk/gov.uk feeds → editorial review queue),
**case-law workflow** (§7, proven with *Jones v Garnett*), and the
**editorial queue UI** — a staff-only web surface at `/monitoring/`
(no longer Django Admin only): the change queue with per-alert
resolve/dismiss forms, notes-and-release enforcement surfaced as
messages, the authority status workflow page, and a nav badge counting
unresolved alerts. View layer and its staff-only access boundary are
tested in `monitoring/tests.py` (`TestEditorialQueueViews`,
`TestOpenAlertBadge`).

1. **CGT/SDLT depth** — **Business Asset Disposal Relief now built**
   (`strategy.cgt_business_asset_disposal_relief`: 14% rate + £1m lifetime
   limit as data, TCGA 1992 ss.169H-169S, golden case + hand-computed
   tests in `test_property.py::TestBadr`, editorially signed off). Still
   open: the 6 April 2026 BADR rate rise to 18% (a future data row, on the
   watch-list); 2024/25 intra-year CGT rates (needs intra-year effective
   ranges); letting-relief edge cases; Scottish LBTT / Welsh LTT variants;
   disposal composition with the salary/dividend whole-income picture.
2. Ops/compliance items before real firms: real SECRET_KEY/env handling,
   MFA, per-client access controls, backups, DPIA, Cyber Essentials —
   architecture doc §7 lists the full set.
3. Phase 2+: MTD API integration; LLM narrative layer with validator
   (architecture doc §8 guardrails); LLM voices for the expert panel
   (explain-only, per §8).

## 7. How case law enters the system

Implemented today (pattern proven with *Jones v Garnett* [2007] UKHL 35,
linked to the salary/dividend strategy):

1. A decision is an **Authority row**: neutral citation, Find Case Law
   URI, verbatim holding, status.
2. Strategies cite it alongside statute; it appears in every report's
   legal basis.
3. When a later decision doubts/overrules it, the tax editor flips the
   authority's `status` — every dependent strategy is then identifiable
   by query (`authority.strategies.all()`) for risk-status review. That
   is how a tribunal loss becomes a `contested` flag on affected advice.

Planned (Phase 2+): Find Case Law feed → LLM *triage* (summarise/classify
only, advisory, per architecture doc §8) → human editor updates authority
status, strategy risk flags, and explanations → new rule-base release →
affected-advice query tells firms which clients to revisit. The court's
*reasoning* never becomes executable logic by itself; it changes risk
classifications and editorial text under four-eyes control. That is
deliberate: reproducibility and PI-defensibility depend on it.
