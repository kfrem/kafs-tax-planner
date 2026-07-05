# UK Tax Planner

Django/PostgreSQL implementation of the architecture in
[`Tax_Planner_Architecture_and_Stack_Recommendation.docx`](Tax_Planner_Architecture_and_Stack_Recommendation.docx):
a versioned, effective-dated UK tax rule base with citations, a deterministic
calculation engine, an immutable advice audit trail, and row-level
multi-tenant isolation, wrapped in a server-rendered Django app.

## Documentation

| Document | Audience / purpose |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System **as built**: components, models, engine, invariants |
| [docs/DEVELOPER_HANDOVER.md](docs/DEVELOPER_HANDOVER.md) | Take-over guide: build log, setup, conventions, defect log, known simplifications, remaining work, case-law roadmap |
| [docs/TEST_EVIDENCE.md](docs/TEST_EVIDENCE.md) | Full test inventory, how to run, expected results, persona suite, manual verification sessions |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Container usage, required environment, UK hosting comparison |
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

Out of scope for this build (per the doc's own phasing): IHT/property
modules, HMRC MTD integration, LLM narrative drafting, practice-management
integrations — all Phase 2/3.

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

## Local setup

Requires: Python 3.11+, Docker (for PostgreSQL), and on Windows, the GTK3
runtime for WeasyPrint (`winget install tschoonj.GTKForWindows` — already
wired into `config/settings.py` via a PATH shim).

```bash
python -m venv venv
source venv/Scripts/activate        # or venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# PostgreSQL (dev)
docker run -d --name taxplanner-pg -e POSTGRES_DB=taxplanner \
  -e POSTGRES_USER=taxplanner -e POSTGRES_PASSWORD=taxplanner_dev_pw \
  -p 5432:5432 postgres:16

# Create a non-superuser app role so PostgreSQL row-level security is
# actually enforced (the POSTGRES_USER role above is a superuser and
# bypasses RLS, so the app must NOT connect as it):
docker exec -it taxplanner-pg psql -U taxplanner -d postgres -c \
  "CREATE ROLE app_user WITH LOGIN PASSWORD 'app_user_dev_pw' CREATEDB;"
docker exec -it taxplanner-pg psql -U taxplanner -d postgres -c \
  "DROP DATABASE taxplanner; CREATE DATABASE taxplanner OWNER app_user; GRANT ALL ON SCHEMA public TO app_user;"
```

Copy `.env.example` to `.env` (dev defaults work with the Docker setup
above) or set your own
`DATABASE_URL=postgres://app_user:app_user_dev_pw@localhost:5432/taxplanner`.

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
python -m pytest
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
