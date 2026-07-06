# UK Tax Planner

Django/PostgreSQL implementation of the architecture in
[`Tax_Planner_Architecture_and_Stack_Recommendation.docx`](Tax_Planner_Architecture_and_Stack_Recommendation.docx):
a versioned, effective-dated UK tax rule base with citations, a deterministic
calculation engine, an immutable advice audit trail, and row-level
multi-tenant isolation, wrapped in a server-rendered Django app.

## Documentation

**New developer? Start with [docs/ONBOARDING.md](docs/ONBOARDING.md)** — the
single front door: the non-negotiable rules, run-from-zero setup, the app
map, current state, deployment, and the tribal knowledge that isn't obvious
from the code.

| Document | Audience / purpose |
|---|---|
| [docs/ONBOARDING.md](docs/ONBOARDING.md) | **Read first.** Seamless take-over guide tying everything together |
| [docs/ENGINEERING_PLAYBOOK.md](docs/ENGINEERING_PLAYBOOK.md) | The binding correctness/governance rules — read before writing code |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System **as built**: components, models, engine, invariants |
| [docs/DEVELOPER_HANDOVER.md](docs/DEVELOPER_HANDOVER.md) | Build log, conventions, defect log, known simplifications, remaining work, case-law roadmap |
| [docs/TEST_EVIDENCE.md](docs/TEST_EVIDENCE.md) | Full test inventory, how to run, expected results, persona suite |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) + [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | Container usage, hosting comparison, and the go-live checklist |
| [docs/HOSTING_AND_COSTS.md](docs/HOSTING_AND_COSTS.md) | Costs per growth stage, database options, provider-switching, and the stack decision log |
| [docs/RULE_BASE_REVIEW_PACK.md](docs/RULE_BASE_REVIEW_PACK.md) + [docs/EDITORIAL_SIGNOFF.md](docs/EDITORIAL_SIGNOFF.md) | The generated editorial review pack and reviewer sign-off history |
| The `.docx` above | The founding design document (pre-build) |

Three canonical test personas (simple / typical / complex —
`python manage.py seed_demo_clients`) keep every engine change verified
across the whole client-complexity range; see TEST_EVIDENCE.md §3.

## What is built (Phase 1 MVP scope)

- **Firms app** — firms, staff accounts with roles (partner/manager/staff),
  PostgreSQL row-level security enforced at the database layer.
- **Authority registry** — first-class citation records (statute, HMRC
  manual, tribunal/court) with status tracking.
- **Rule engine** — effective-dated `TaxParameter` rows (PostgreSQL date
  ranges), `Strategy` rows carrying timeframe/risk/DOTAS/GAAR flags, and a
  pure-Python calculation engine (`ruleengine/calculators.py`) covering:
  - Income tax (with personal allowance taper)
  - Dividend tax
  - Combined whole-person tax (`combined_personal_tax`): earned income and
    dividends computed together — PA tapered on total income including
    dividends, unused PA sheltering dividends, dividends stacked above
    earned income in the bands. The salary/dividend and incorporation
    strategies quantify the *incremental* tax an extraction causes on top
    of the client's other income (sole trade, employment), not each income
    source in isolation.
  - Employee & employer Class 1 NIC (with Employment Allowance)
  - Class 4 NIC
  - Corporation tax with marginal relief
  - Pension annual allowance with 3-year carry-forward and tapering
  - **Strategies**: salary/dividend extraction mix, pension carry-forward,
    incorporation vs. sole trade, Marriage Allowance transfer
- **Client data module** — manual entry + CSV import, versioned per tax year.
- **Advice generator** — matches eligible strategies, quantifies them,
  writes an **append-only** `AdviceRecord` (input hash/snapshot, rule-base
  version, citations, results). Records cannot be edited or deleted.
- **Branded PDF reports** via WeasyPrint, generated from the same data as
  the web view.
- **Golden regression tests** — hand-verified worked examples plus a
  data-driven runner over `GoldenTestCase` rows (the CI gate described in
  Section 5.5 of the architecture doc).

> **Scope has grown well beyond this original Phase-1 list.** Now also
> built: the full **IHT** and **property/CGT/SDLT** modules (BADR, lettings
> relief, PPR, spousal transfer; SDLT/LBTT/LTT residential, commercial and
> lease-NPV across all three UK jurisdictions), intra-year and future-year
> effective dating, change-monitoring watchers with an editorial queue UI,
> MFA, and a `/healthz` probe — 20 strategies, 218 tests. See
> [docs/ONBOARDING.md](docs/ONBOARDING.md) §6 for the current picture.
> Still out of scope (Phase 2/3): HMRC MTD integration, LLM narrative
> drafting, practice-management integrations.

## Governance warning — read before using this for a real client

The rule base is seeded from real, published 2024/25 and 2025/26 HMRC/
legislation figures, but **it has not been reviewed by a qualified tax
professional**. The architecture doc is explicit (Section 5.6) that a named
tax editor and a distinct second reviewer must check every parameter and
citation against the primary source before a rule-base release goes live.
`seed_rule_base` creates releases as **DRAFT** by default for exactly this
reason — advice generation will refuse to run (`NoReleasedRuleBaseError`)
until someone reviews the data in `/admin/` and marks a
`RuleBaseRelease` as **Released** with a reviewer distinct from the editor.
The `--release` flag exists only to make local development/testing possible
without doing that review; never use it against real client data.

## Mandatory self-audit — the app checks itself; never skip it

This is intended to be the first tool of its kind in the UK: it produces the
very numbers an accountant hands a client, across potentially thousands of
companies, so **a single wrong penny is a real defect, not a rounding quibble.**
Every change — however small, and however certain you are it "cannot change the
result" — must pass the self-audit before it is done. This is not optional and
does not depend on who is doing the work.

```bash
python manage.py migrate                    # apply ALL migrations FIRST (see below)
python manage.py seed_rule_base --release   # dev/test only (see governance warning)
python manage.py seed_watched_sources
python manage.py run_watchers               # fetch primary-source snapshots (network)
python manage.py self_audit --passes 3      # the app audits itself, end to end, 3x
```

`self_audit` (`advice/management/commands/self_audit.py`) builds **real client
cases** (`advice/audit_cases.py`) that between them exercise **every** registered
strategy, and for each case it regenerates the advice, renders the PDF, deploys
the four-expert panel, and has the panel **independently recompute every figure
from the stored input snapshot**. It exits non-zero on ANY of:

- an **unapplied migration** — the exact defect that once let the app 500 in the
  browser while every unit test still passed (see below);
- a golden-case mismatch or an editorial machine-pre-check failure;
- a panel *engine-defect* finding — a figure that does not reproduce, extraction
  arithmetic that does not balance, missing provenance, or an uncited position;
- a non-deterministic recomputation (same facts producing different numbers);
- a PDF that fails to render;
- any live strategy that **no** real case exercises end to end.

The same audit runs on every push (`advice/tests/test_self_audit.py`), including a
negative test proving it actually *rejects* a broken rule base. Run it locally with
`--passes 3` before handing over, so you have **seen** it green several times — the
way an agent re-checks its own work rather than trusting a single pass.

### Why `migrate` is called out first
A database that is behind on migrations passes the *entire* unit-test suite (the
test DB is rebuilt fresh from migrations every run) while the real app 500s on the
first authenticated page. That happened once — the `django_otp` (MFA) tables were
never created in the dev DB. `self_audit` now refuses to pass while any migration is
unapplied, so it cannot recur regardless of who takes over. **Always run
`python manage.py migrate` after pulling changes, before anything else.**

### Definition of done for every change (restated, binding)
1. Implementation + rule data (rates as data, effective-dated per `docs/ENGINEERING_PLAYBOOK.md`).
2. Hand-computed tests **and** a golden case pinning each new figure.
3. Full suite green (`pytest`) — never run two pytest processes against the shared DB at once.
4. Docs updated: coverage map, `TEST_EVIDENCE.md`, `EDITORIAL_SIGNOFF.md`, review pack.
5. Governance pipeline: `ruff`, `check --deploy`, reseed, `seed_watched_sources`,
   `run_watchers`, `generate_review_pack` (0 machine failures), sign-off restored,
   any `ChangeAlert` triaged with recorded notes.
6. **`python manage.py self_audit --passes 3` green**, and — for anything with a UI
   effect — actually opened in the browser and confirmed to render without errors.

## Local setup

Requires: Python 3.13, Docker (for PostgreSQL), and on Windows, the GTK3
runtime for WeasyPrint (`winget install tschoonj.GTKForWindows` — already
wired into `config/settings.py` via a PATH shim).

```bash
python -m venv venv
source venv/Scripts/activate        # or venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# PostgreSQL 16 on host port 5433 (avoids clashing with any other local
# Postgres on 5432). The compose db service provisions the non-superuser
# app_user role for you via docker/init-app-user.sql, so RLS is real:
docker compose up -d db
```

Copy `.env.example` to `.env` (dev defaults expect the DB on port **5433**:
`DATABASE_URL=postgres://app_user:app_user_dev_pw@localhost:5433/taxplanner`).
The current dev container is named `taxplanner-pg` (postgres:16) mapped
`5433->5432`; see [docs/ONBOARDING.md](docs/ONBOARDING.md) §8 for how to
recreate it keeping the data volume.

```bash
python manage.py migrate
python manage.py seed_rule_base --release   # --release: dev/test only, see warning above
python manage.py createsuperuser            # optional, for /admin/
python manage.py runserver
```

Log in at `/accounts/login/`. The seed command also creates `tax_editor` /
`tax_reviewer` superuser accounts (passwords `changeme-tax-editor` /
`changeme-tax-reviewer`) for `/admin/` rule-base editing — change these
immediately in any shared environment.

To try the golden path: create a firm-linked user
(`Firm.objects.create(...)`, then `User.objects.create_user(..., firm=firm)`
via `manage.py shell`), log in, create a client, record facts for a tax
year, click "Generate advice".

## Tests

```bash
python -m pytest        # expect: 218 passed (~6 min); this is the reproduction checkpoint
```

Covers: calculator correctness against hand-verified HMRC-rate worked
examples, the data-driven golden-case runner, row-level security isolation
(firm A cannot see firm B's data, verified at the database level, not just
in application code), CSV import, advice generation/eligibility matching,
advice-record immutability (append-only, undeletable), and PDF rendering.

## Key architectural decisions carried over from the design doc

- **Rules are data, not code**: `TaxParameter`/`Strategy` rows in Postgres,
  edited via Django Admin, not hard-coded — see `ruleengine/models.py`.
- **Row-level security in the database**, not only in views —
  `firms/middleware.py` sets `app.current_firm_id` per request;
  `clients/migrations/0003_row_level_security.py` and
  `advice/migrations/0004_row_level_security.py` enforce it with
  `FORCE ROW LEVEL SECURITY` (required because the owning role would
  otherwise bypass its own policies).
- **Immutable advice records** — `advice/models.py` overrides `save()`/
  `delete()` to make `AdviceRecord` genuinely append-only in code, not just
  by convention.
- **No LLM anywhere in this build** — deliberately deferred per Section 8;
  the deterministic engine is authoritative for every number, citation, and
  risk flag.
