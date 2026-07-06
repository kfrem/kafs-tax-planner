# Test evidence

The complete testing record: what is tested, how to run it, what the
expected results are, and the manual verification sessions performed
during the build. A new developer should be able to reproduce every result
on this page.

## 1. How to run

Prerequisites: the PostgreSQL container and venv from README "Getting
started" (tests create their own `test_taxplanner` database; the app role
needs CREATEDB, which the README setup grants).

```bash
source venv/Scripts/activate
python -m pytest -q               # full suite
python -m pytest -q --create-db   # force-rebuild the test DB after migrations change
python -m pytest -q ruleengine/tests/test_iht.py   # one module
```

**Expected result: `210 passed`** (≈6 minutes; the seed fixture rebuilds
the rule base per test class, which dominates runtime).

The same suite runs in **GitHub Actions on every push and pull request**
(`.github/workflows/ci.yml`): PostgreSQL 16 service container, a
non-superuser app role so the RLS tests exercise real enforcement, and
`pytest -q`. Repository: https://github.com/kfrem/kafs-tax-planner.

Last full run: **210 passed, 0 failed, 0 skipped** —
locally (Python 3.13.14, Django 6.0.6, PostgreSQL 16/Docker, Windows 11)
and in CI (ubuntu-latest, Python 3.13), 6 July 2026.

## 2. Test inventory (210 tests)

| File | Tests | What it proves |
|---|---|---|
| `ruleengine/tests/test_calculators.py` | 14 | Layer 2 calculators against hand-computed 2025/26 values: income tax incl. PA taper, dividend tax, employee/employer NIC (incl. 2025/26 threshold change + Employment Allowance), Class 4, CT marginal relief, pension AA taper |
| `ruleengine/tests/test_golden_cases.py` | 2 (data-driven) | Executes all **28 GoldenTestCase rows stored in the rule base itself** (each with its own `tax_year`, so 2026/27 and 2024/25 cases run against those years' rows) — the §5.5 release gate. Adding a golden case to the seed automatically adds coverage |
| `ruleengine/tests/test_income_interaction.py` | 11 | Whole-income interaction: PA taper triggered by dividends, PA remainder sheltering dividends, Sarah's exact scenario to the penny, optimiser (interior optimum at £5,000; £12,570 confirmed optimal when no other income; affordability cap £9,347 from £10,000 profit) |
| `ruleengine/tests/test_pension_relief.py` | 6 | RAS band extension (40% relief case), taper restoration (60% effective relief case), FA 2004 s.190 earnings cap, £3,600 floor, AA charge basis, employer-route CT saving |
| `ruleengine/tests/test_iht.py` | 12 | Estate calculator (NRB/RNRB, home-equity cap, descendants condition, £2m taper, spouse exemption, 36% boundary) and all three IHT strategies incl. RNRB-restoration-by-gift |
| `ruleengine/tests/test_provenance.py` | 5 | Draft releases never influence calculations; released rows do; provenance logs exact row ids/releases and survives cache hits |
| `ruleengine/tests/test_property.py` | 38 | CGT band straddling, AEA, PPR relief with the final-9-months rule, spousal transfer (both the honest £720 both-higher-rate case and the basic-rate-spouse case), SDLT bands, 5% surcharge, FTB relief and its price cap; **Business Asset Disposal Relief** (`TestBadr`): qualifying gain within the £1m limit at 14% vs 24% unrelieved (saving £49,700), excess over the limit at the standard rate (£1.2m gain → saving £100,000), and a partly-used lifetime limit (£700k prior → saving £30,000), all hand-computed; **Scottish LBTT** (`TestLbtt`): standard purchase (£350k → £8,350, genuinely differing from the £7,500 SDLT), FTB relief worth £600, 8% ADS on the whole price; **Welsh LTT** (`TestLtt`): main rates (£400k → £10,500) and the separate higher-rate table for additional dwellings (£400k → £29,950); **lettings relief** (`TestLettingsRelief`): the HS283 shared-occupancy example (60/40, £60k gain → £24k relief, £12k chargeable, saving £5,760) plus the two other binding branches of the lowest-of-three (£40k cap; PPR the minimum); **non-residential land taxes** (`TestNonResidentialLandTax`): a £500k commercial freehold under all three regimes (SDLT £14,500, LBTT £13,500, LTT £12,750) plus Wales's 6% top band (£1.5m → £67,750); **2026/27 release scaffolding** (`TestFutureYearBadr`): BADR resolves 14% for 2025/26 and 18% for 2026/27 across two effective-dated rows (£500k disposal → £69,580 vs £89,460), and an unapproved 2026.1 release is invisible to the engine (four-eyes); **2024/25 intra-year CGT** (`TestIntraYearCgt2024`): the 30 Oct 2024 non-residential change resolved by disposal date (£17k gain → £1,700 before, £3,060 after), residential unchanged across the boundary, and an `as_of` outside the tax year rejected, all hand-computed |
| `monitoring/tests.py` | 34 | Change watchers: baseline-then-detect with unified diffs, cosmetic-markup changes suppressed, fetch failures skipped not fatal; feed-specific fetchers (legislation.gov.uk XML API first with page fallback, gov.uk content API extraction, per-type resolver, --rebaseline for representation changes); authority status workflow (append-only log, reason required, editorial alert raised); editorial workflow (notes required, actioned requires a release); watched-source seeding idempotent; alert → dependent-strategies impact link. **Editorial queue UI** (`TestEditorialQueueViews`): queue and authorities pages render for staff; `alert_action` mark-under-review / dismiss / action-with-release through the form; failure modes surfaced as error messages not 500s (dismiss without notes, action without release both leave the alert open); GET on the action endpoint is 405; **staff-only access boundary** — a firm user (`is_staff` False) and anonymous are both redirected, and a firm user's POST cannot change an alert. **Nav badge** (`TestOpenAlertBadge`): the open-alert count is computed for staff only, excludes resolved alerts, is zero for firm users and anonymous, and renders in the chrome |
| `advice/tests/test_generator.py` | 5 | Generator pipeline: eligibility, immutability (save/delete refusal), supersession, release stamping |
| `advice/tests/test_personas.py` | 19 | **The consistency suite** — see §3 |
| `advice/tests/test_adapters.py` | 5 | Fact-schema fields reach the right calculator inputs; employment income counts as relevant UK earnings, 'other income' (rent/savings) does not |
| `advice/tests/test_impact.py` | 6 | Release impact alerts: strategy overlap detection, effective-dating scoping (a 2026/27 change never alerts 2025/26 advice), idempotency, superseded advice excluded, review workflow |
| `advice/tests/test_scenarios.py` | 5 | Scenario modelling: overrides applied without mutating the record, deltas correct (hand-computed), NOTHING persisted, and the base leg byte-identical to real advice |
| `advice/tests/test_narrative.py` | 8 | Narrative drafter + §8 validator: draft carries the record's headline figures and risk disclosures; fabricated numbers/citations rejected; rejected drafts cannot be stored; panel persona voices re-express findings verbatim, never add |
| `firms/test_mfa.py` | 7 | TOTP MFA: QR enrolment, wrong-token refusal, enforcement for device holders, verification unlock, logout always reachable, no prompt for non-enrolled users |
| `clients/test_access.py` | 4 | Per-client access: partners see all, staff only granted clients (list, detail, advice, scenario views all enforce), grant management partner-only |
| `advice/tests/test_panel.py` | 12 | **Expert panel**: per-persona verdicts across all three personas (Emma clear, Sarah/Victor attention with specific finding codes); blockers on rule drift (independent recomputation) and on an overruled authority; decision workflow gating (no decision without a review, blocker override needs a written note, reject/revise need notes); panel reviews append-only |
| `clients/tests.py` | 4 | Fact-set versioning, CSV import |
| `firms/tests.py` | 3 | Row-level security: cross-firm reads/writes blocked at the database |
| `reports/tests.py` | 1 | PDF renders and attaches to the record |

Conventions: every numeric expectation is **hand-computed from published
rates with the working shown in a comment** — tests assert what the law
says, not what the code returned last time. Tolerance is ±£0.02
(`pytest.approx`) for penny-rounding only.

## 3. The persona consistency suite

Three canonical clients (`clients/personas.py`) bracket the complexity
range and are regenerated by `python manage.py seed_demo_clients`:

| Persona | Profile | Pinned expectations (examples) |
|---|---|---|
| **Emma Hughes** (H001, simple) | Part-time employee £9k, spouse £30k, £2k pension wish | Exactly 2 strategies fire (nothing over-fires on a simple client); Marriage Allowance eligible, saving £252.00; pension relief = £400 basic credit, no employer route |
| **Sarah Mitchell** (M042, typical) | Company £95k profit, £28k sole trade, spouse £11k, £40k pension wish, £1.9m household estate | Optimal salary £5,000 (net £54,017.50); pension capped at £28k relevant earnings, employer route saves £10,600; transferable IHT bands worth £200,000; gift saves £40,000 |
| **Victor Adeyemi** (A007, complex) | Company £480k, £85k sole trade, £30k rental, tapered AA, £4.5m estate | AA tapered to £15k (+£90k carry-forward = £105k, £15k excess exposed); relief capped at £85k earnings, £35k unrelieved, employer route saves £30,000; RNRB tapered to **zero**; charity top-up: £335k extra legacy costs family £62,400 net |

Cross-persona structural invariants (parametrised over all three):
- every strategy result carries ≥1 citation, a valid risk status, and a
  timeframe; provenance is non-empty and fully release-attributed;
- **determinism**: generating twice from the same facts yields identical
  results, provenance, and input hash;
- **accounting identity**: for every optimiser comparison row,
  net = salary + dividends − employee NIC − personal tax, to the penny.

## 4. Manual verification sessions (beyond the automated suite)

Performed during the build, reproducible from the repo:

1. **UI walkthrough** — login, client creation, fact entry, advice
   generation, PDF download, all via the browser against the dev server;
   RLS verified the hard way (a shell without firm context was refused by
   PostgreSQL).
2. **Sarah end-to-end** — advice records regenerated after each engine
   improvement; her audit chain (records 2→…→10, two tax years, three
   rule-base versions) demonstrates supersession with full history.
3. **Simulated Budget cycle** — dividend allowance abolished + rates +2pts
   for 2026/27 under a simulation release: impact analysis by query
   (5 calculators, 3 strategies, 7 advice records identified), old rows
   closed not deleted, 2026/27 advice repriced (−£1,441.75/yr for Sarah),
   2025/26 results byte-identical afterwards, simulation reverted, and the
   affected advice record superseded (deletion correctly refused by the
   model). This session is what motivated the provenance/draft-gating work
   (defect F3 in DEVELOPER_HANDOVER.md §4).
4. **PDF inspection** — reports rendered to images and checked page by
   page (branding, risk flags, citations, rule-provenance table).

## 5. Reproducing the manual sessions

```bash
python manage.py seed_rule_base --release
python manage.py seed_demo_clients      # regenerates persona advice + PDFs
python manage.py runserver              # demo / demo-pass-123
```

Then compare the persona advice records on screen (or the PDFs in
`media/advice_reports/`) against the pinned numbers in §3 — they must
match exactly. If they don't, a rule-base or engine change has altered
behaviour and `pytest` will be failing too; that coupling is deliberate.
