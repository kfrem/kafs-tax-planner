# Developer onboarding — start here

If you have just been handed this repository, read this file first. It is
the single front door: it tells you what the project is, the rules you must
not break, how to get running in ~15 minutes, where everything lives, what
state it is in today, and how to deploy it. Everything else is linked from
here.

Last updated: 25 July 2026.

---

## 1. What this is (and the one rule that matters most)

A UK tax-planning decision-support web app for accounting firms. It takes a
client's facts for a tax year, applies a versioned, effective-dated rule
base, and produces quantified planning advice with citations and a branded
PDF — with every figure traceable to legislation and reproducible forever.

**The prime directive:** every number the tool shows carries professional
liability, so *correctness is provable, not asserted*. That single idea
drives all the unusual rules below. If you break them, the product's whole
value proposition ("I can show HMRC exactly why this number is right")
breaks with it. These are non-negotiable — they are written up in full in
[`ENGINEERING_PLAYBOOK.md`](ENGINEERING_PLAYBOOK.md) and you must follow
them:

- **Rates and rules are data, not code.** Tax rates/thresholds live in
  `TaxParameter` database rows with effective-from/to dates. A rate change
  is a *new row*; the old row is closed (never edited or deleted) so past
  computations stay reproducible. If you find yourself editing a calculator
  for a rate change, stop — the design is wrong or you are.
- **Hand-compute every test expectation.** A test asserts what the
  legislation says, worked out by hand (or from a published HMRC example),
  with the working shown in a comment — never what the code returned last
  time. Snapshot tests are banned.
- **Golden cases live in the database and run in CI.** Adding a
  `GoldenTestCase` row automatically adds coverage.
- **Outputs that matter are append-only.** `AdviceRecord` refuses updates
  and deletes in the model layer; corrections are new records. Do not try
  to "fix" one by editing it.
- **Four-eyes rule governance.** `seed_rule_base` creates releases as
  DRAFT; draft rows are invisible to the engine. A named editor plus a
  distinct reviewer approve each release (via `/monitoring/` or Admin)
  before it can produce advice. `--release` bypasses this for dev/test
  only — never against real client data.
- **Definition of done for any change — all six:** implementation ·
  hand-computed tests · invariants still green · docs updated · defect log
  updated if anything was found · CI green.

## 2. Read these next, in this order

| Doc | What it gives you |
|---|---|
| [`ENGINEERING_PLAYBOOK.md`](ENGINEERING_PLAYBOOK.md) | The binding rules above, in full. Read before writing code. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | The system as built: components, models, engine, the invariants that must never break. |
| [`DEVELOPER_HANDOVER.md`](DEVELOPER_HANDOVER.md) | Build log, conventions, the **defect log (F1–F8)**, known simplifications (§5), remaining work (§6), case-law roadmap (§7). |
| [`TEST_EVIDENCE.md`](TEST_EVIDENCE.md) | Every test file and what it proves; how to run; expected result. |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) + [`PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md) | How to run the container anywhere; the go-live checklist (what's done in code vs what the firm/host must sign off). |
| [`RULE_BASE_REVIEW_PACK.md`](RULE_BASE_REVIEW_PACK.md) + [`EDITORIAL_SIGNOFF.md`](EDITORIAL_SIGNOFF.md) | The machine-generated review pack and the reviewer's sign-off history. |

## 3. Get running in ~15 minutes (from zero)

Prerequisites: **Python 3.13**, **Docker Desktop** (for PostgreSQL), and on
Windows the **GTK3 runtime** for WeasyPrint PDF rendering
(`winget install tschoonj.GTKForWindows`; a PATH shim in `config/settings.py`
wires it in).

```bash
# 1. Python env
python -m venv venv
source venv/Scripts/activate            # Windows Git Bash; use bin/activate on macOS/Linux
pip install -r requirements.txt

# 2. PostgreSQL 16 on host port 5433 with the non-superuser app role
#    (RLS is only real if the app does NOT connect as a superuser).
#    Easiest: the compose db service, which runs the init-app-user.sql for you:
docker compose up -d db                 # provisions app_user automatically
#    (This repo's dev .env expects the DB on localhost:5433 — see note below.)

# 3. Database + data
python manage.py migrate
python manage.py seed_rule_base --release    # DRAFT by default; --release is dev/test only
python manage.py seed_demo_clients           # Emma / Sarah / Victor + advice + PDFs

# 4. Prove you reproduced the build
python -m pytest -q                     # expect: 334 passed  (~8 min; the seed rebuilds per test class)
python manage.py runserver              # http://localhost:8000
```

Reproduction check: **334 passing means you have byte-for-byte the same
calculation behaviour this build has** — every expectation is a
hand-computed number.

**Important port note:** the dev `.env` uses
`DATABASE_URL=postgres://app_user:app_user_dev_pw@localhost:5433/taxplanner`
(port **5433**, chosen so it never clashes with any other local Postgres on
5432). The currently-running dev container is named `taxplanner-pg`
(postgres:16) mapped `5433->5432`. If you ever need to recreate it keeping
the data volume, see §8. The old README examples used 5432 — 5433 is
correct.

## 4. Where everything lives (app map)

| Django app | Responsibility |
|---|---|
| `firms/` | Firms, staff users + roles, **row-level security middleware**, MFA (TOTP). |
| `authority/` | Citation registry (statute / HMRC manual / court judgment) with status workflow. |
| `ruleengine/` | The heart: `models.py` (TaxParameter, Strategy, RuleBaseRelease, GoldenTestCase), `engine.py` (`get_parameter`, calculator registry, provenance), `calculators.py` (all pure calculation + strategy functions), `editorial.py` (machine pre-check), `taxyear.py`, and the `seed_rule_base` / `generate_review_pack` management commands. |
| `clients/` | Client records, fact entry, CSV import, the demo personas. |
| `advice/` | Advice generator, append-only `AdviceRecord`, strategy adapters (facts → calculator inputs), scenarios, impact alerts, the expert-panel validator. |
| `reports/` | Branded PDF rendering (WeasyPrint). |
| `monitoring/` | Change watchers over primary sources, the editorial change queue UI, authority status workflow. |
| `config/` | Settings, URLs, WSGI, and the `/healthz` probe. |

The calculation flow: a `Strategy` row names a `calculator_key`; the
calculator reads rates only through `get_parameter(key, tax_year, as_of=…)`
so every calculator is registered against the parameters it consumes (this
is what makes "which advice is affected if this rule changes?" a query, not
a memory exercise). An **adapter** (`advice/strategy_adapters.py`) maps a
client's nested facts to the calculator's flat inputs and decides
eligibility.

## 5. How to add a new tax rule or strategy (the recipe)

A new strategy is **six things — no exceptions** (worked examples to copy:
BADR, lettings relief, the devolved land taxes, all added recently):

1. a **calculator** in `ruleengine/calculators.py` (pure, deterministic,
   reads params via `get_parameter`);
2. an **adapter** in `advice/strategy_adapters.py`;
3. a **Strategy row** in `seed_rule_base.py` (code, calculator_key,
   timeframe, risk, plain-English explanation ≥150 chars, authorities);
4. **authorities** (Authority rows + watched source) — or reuse existing;
5. a **golden case** (`GoldenTestCase` row, hand-verified);
6. **hand-computed tests** with the working in comments.

Then: update the editorial strategy-count assertion in
`ruleengine/tests/test_editorial.py`, run the suite, regenerate the pack
(`manage.py generate_review_pack`), and update the docs. A rate change for a
*new tax year* is a new effective-dated row under a new `RuleBaseRelease`
(see BADR 2026/27 and the dividend 2026/27 rise for the pattern; the engine
resolves any year, and any intra-year date via `as_of`).

## 6. Current state (what is actually built now)

Far more than the original README's "Phase 1" scope. As of this handover:

- **Personal tax** — income tax (PA taper), dividend tax, NIC (employee /
  employer / Class 4), corporation tax with marginal relief, pension annual
  allowance with carry-forward + taper, combined whole-person tax.
- **Strategies (20)** — salary/dividend mix, pension carry-forward,
  incorporation vs sole trade, Marriage Allowance; **IHT** (spouse
  transfer, lifetime gifting, 36% charitable rate); **CGT** (PPR relief with
  final-9-months, spousal transfer, **BADR**, **lettings relief**);
  **land taxes** — SDLT/LBTT/LTT for residential, commercial freehold, and
  **lease NPV**, all three UK jurisdictions.
- **Effective-dating** spans **intra-year** (30 Oct 2024 CGT change),
  **year-boundary**, and **future-year** changes (BADR 18% and dividend
  +2pp from 6 April 2026 under release 2026.1). Six releases: 2024.1,
  2024.2, 2025.1, 2025.2, 2025.3, 2026.1.
- **CGT composition** — a gain stacks above the client's whole income
  (earned + dividends), band extended by pension contributions.
- **Governance & ops** — change-monitoring watchers → editorial queue UI at
  `/monitoring/` (staff-only), machine pre-check + review pack, MFA,
  row-level multi-tenant isolation, append-only audit trail with provenance,
  `/healthz` probe.
- **Tests: 334 passing**; 71 golden cases; 64 authorities (each watched,
  with fetched primary-source snapshots); **51 live strategies**; editorial
  pre-check reports **0 machine-check failures**. CI green on every push.
- **25 July 2026 additions** — SDLT uninhabitable/derelict classification
  (FA 2003 s.116, the *Bewley* principle, borderline) and the FHL abolition
  transitional (Finance Act 2025 Sch 5). Only remaining coverage-map gap is
  charity VAT, which needs a VAT module the app does not have — a documented
  scoping deferral (see DEVELOPER_HANDOVER §6, task list).
- **July 2026 additions** — income timing across tax years (prices the
  April-2026 dividend rise), Payroll Giving, gifts of shares/property to
  charity (ITA 2007 s.431 + TCGA 1992 s.257 double relief), business-asset
  rollover relief (TCGA 1992 s.152), **full expensing** (CAA 2001 s.45S),
  **holding-company structuring** (CTA 2009 Part 9A) and **SDLT mixed-use
  classification** (borderline) — plus the editorial next-cycle refinements
  (review-pack key ordering, `cgt.rates` label, s.850C / FA 2004 s.197 /
  LBTT Sch 2A / LTT Sch 5 citations) and the Django 6.0.7 security bump.

Recent sessions are summarised in `DEVELOPER_HANDOVER.md §6` and the
`EDITORIAL_SIGNOFF.md` addenda.

## 7. Deployment & go-live

The app ships as one Docker image (see `Dockerfile`, `docker-compose.yml`).
CI builds it on every push. The go-live plan and hosting comparison are in
`DEPLOYMENT.md`; the split of "done in code" vs "firm/host must sign off"
(DPIA, Cyber Essentials, managed UK Postgres with tested restores, processor
agreement, a four-eyes-released rule base) is in `PRODUCTION_READINESS.md`.

Key framing for whoever takes this to market: **demos use the three dummy
personas, so no real client data and no heavy compliance is needed to start
showing firms.** The compliance pack only applies once a firm signs and real
data goes on.

**Costs, the database options (Neon/Supabase/host-managed), how easy it is
to switch provider as you grow, and the running decision log are all in
[`HOSTING_AND_COSTS.md`](HOSTING_AND_COSTS.md)** — read it before making any
hosting choice so you don't re-litigate settled reasoning. In short: ~£5–10/mo
at demo, ~£10–30/mo at 2–5 firms, ~£30–100/mo at 10+; switching host is a
Docker redeploy plus a `pg_dump`/`pg_restore` (~half a day), by design.

## 8. Accounts, environment, and CI

- **Repo:** `https://github.com/kfrem/kafs-tax-planner`. Work happens on
  `main`; **an auto-saver commits frequently** (`auto: save …`) — that is
  expected, not someone else's work.
- **CI is the authoritative test gate.** GitHub Actions runs the full suite
  against its own PostgreSQL service on every push, plus `check --deploy`,
  `ruff`, `pip-audit`, and `docker build`. A red build means do not merge.
  Local Docker is only for faster local runs.
- **Environment:** copy `.env.example` → `.env`. Required for any host:
  `DATABASE_URL` (non-superuser role), a real per-environment `SECRET_KEY`,
  `DEBUG=false`, `ALLOWED_HOSTS`. Under `DEBUG=false` the settings enable
  SSL redirect, secure cookies and HSTS automatically (`check --deploy`
  reports 0 warnings with a real key).
- **Seed accounts (change every password in any shared environment):**
  `seed_rule_base` creates `tax_editor` / `tax_reviewer` superusers
  (placeholder passwords `changeme-…`) for rule-base review; a local
  `editor` superuser and a `demo` firm user exist in the current dev DB for
  clicking around. None of these are for production.

## 9. Tribal knowledge / gotchas (things not obvious from the code)

- **Docker Desktop on the current Windows machine has been flaky** — it can
  crash on startup with a stale Unix-socket file
  (`…\AppData\Local\Docker\run\…` or `…\docker-secrets-engine\engine.sock`,
  "the file cannot be accessed by the system"). Fix: quit Docker, run
  `wsl --shutdown`, rename the offending `run` / `docker-*` directory so
  Docker recreates it, relaunch. Docker auto-start on login is now enabled
  and the `taxplanner-pg` container has restart policy `unless-stopped`, so
  after a reboot the DB comes back on its own — just give Docker ~30–60s.
- **Recreating the DB container on 5433 keeping data** (anonymous volume):
  `docker stop/rm taxplanner-pg` then
  `docker run -d --name taxplanner-pg -p 5433:5432 -e POSTGRES_DB=taxplanner -e POSTGRES_USER=taxplanner -e POSTGRES_PASSWORD=taxplanner_dev_pw -v <volume>:/var/lib/postgresql/data postgres:16`
  (find `<volume>` via `docker inspect taxplanner-pg`).
- **The review pack is regenerated, not hand-edited.** After any rule-base
  change: `manage.py generate_review_pack` rewrites
  `RULE_BASE_REVIEW_PACK.md`; the reviewer then fills the sign-off table row
  at the bottom. The pack's "primary source fetched by watcher" lines need
  snapshots on file, which come from `manage.py run_watchers` (hits the
  network — never run watchers inside tests; fetchers are injectable/stubbed
  there).
- **WeasyPrint** needs the native GTK/Pango libraries — the `Dockerfile`
  installs them; on Windows use the winget GTK runtime. `gunicorn` runs only
  in the container (not native Windows); local dev uses `runserver`.
- **The suite takes ~6 minutes** because the `seeded_rule_base` fixture
  rebuilds the rule base per test class. Do not run several pytest processes
  at once against the same Postgres — they collide on the test database.
