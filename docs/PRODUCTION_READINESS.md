# Production readiness checklist

Single source of truth for "are we ready to run this for a real firm with
real client data?" It separates what the **code** already guarantees (done,
tested, in this repo) from what the **firm / host** must do before go-live
(organisational and infrastructure controls that cannot live in code).

Last reviewed: 6 July 2026.

---

## A. Done in code (verified, in this repo)

| Area | What's in place | Evidence |
|---|---|---|
| **Secrets** | `SECRET_KEY` is read from the environment with no fallback; the app refuses to start without it. `DEBUG` defaults to `False`. | `config/settings.py` |
| **Transport security** | With `DEBUG=False` the settings enable `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and HSTS (1 year, `includeSubDomains`, `preload`). `manage.py check --deploy` reports **0 warnings** under production flags with a real key. | `config/settings.py` (`if not DEBUG:` block) |
| **Multi-tenant isolation** | PostgreSQL row-level security keyed to a per-request session variable; the app connects as a **non-superuser** role. Cross-firm reads/writes fail *at the database*, proven by tests. | `firms/middleware.py`, `firms/tests.py` |
| **MFA** | TOTP via `django_otp`; an enforcement middleware requires verification for any user with a confirmed device. | `firms/mfa.py`, `firms/test_mfa.py` |
| **Audit trail** | Advice records, postings and filed outputs are append-only (update/delete refused in the model layer); every output stores provenance (input hash + exact rule rows + release + who + when) and recomputes reproducibly. | `advice/models.py`, `advice/tests/test_generator.py`, `test_provenance.py` |
| **Rule governance** | Rates/rules are data with effective dates; unapproved (draft) releases are invisible to the engine; a machine pre-check + editorial pack gate every release under four-eyes review. | `ruleengine/engine.py`, `ruleengine/editorial.py`, `docs/RULE_BASE_REVIEW_PACK.md` |
| **Session controls** | 8-hour session cap (§7.2). | `config/settings.py` |
| **Health probe** | Unauthenticated, side-effect-free `/healthz` returns 200 with a DB check, 503 if the database is unreachable — for load balancers / orchestration. | `config/health.py`, `firms/tests.py` |
| **Container** | Single Docker image (zero host lock-in); `collectstatic` at build time, WhiteNoise serves static at runtime; entrypoint waits for the DB and applies migrations; gunicorn serves. | `Dockerfile`, `docker/entrypoint.sh` |
| **CI** | Full test suite + `check --deploy` + `ruff` + `pip-audit` + `docker build` on every push; red blocks merge. | `.github/workflows/` |
| **Tests** | 218 hand-computed tests, 33 golden cases in CI; determinism, accounting identities and disclosure invariants enforced across three canonical personas. | `docs/TEST_EVIDENCE.md` |

## B. Firm / host must complete before go-live (not code)

These are organisational or infrastructure controls. They cannot be
"finished" in the repository; each needs an owner and a dated sign-off.

| # | Item | Owner | Notes |
|---|---|---|---|
| 1 | **Rule-base release approved** | Tax editor + second reviewer | Work through `RULE_BASE_REVIEW_PACK.md`; flip the `RuleBaseRelease` status to *released* in Admin (four-eyes). No advice is generated from a draft release. Re-do for every new release. |
| 2 | **Managed PostgreSQL in a UK region** | Host | With **tested restores**, not just backups. Confirm the app role is a non-superuser. See `docs/DEPLOYMENT.md`. |
| 3 | **Real per-environment `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `DEBUG=false`** | Deployer | Never reuse the dev key. `ALLOWED_HOSTS` must include the load-balancer probe host. |
| 4 | **TLS terminated at the edge** | Host | HSTS is emitted by the app; the edge must actually serve HTTPS only. |
| 5 | **DPIA** completed and signed | Firm (data controller) | The firm is the UK GDPR controller; this software is the processor. |
| 6 | **Art. 28 processor agreement** from the host | Firm + host | Required before client personal data lands on the host. |
| 7 | **Cyber Essentials** (or equivalent) | Firm | Expected on small-firm due-diligence checklists. |
| 8 | **Incident-response procedure** | Firm | Who does what on a breach/outage; contact tree; regulator-notification timing. |
| 9 | **Backup + restore drill** run and evidenced | Host + firm | A backup you have never restored is not a backup. |
| 10 | **Scheduled `run_watchers`** | Deployer | Daily, plus a manual run on Budget/fiscal-event days, so legislation changes reach the editorial queue. |
| 11 | **Admin/MFA onboarding** for the tax editor and reviewer | Firm | Set strong passwords (the seed creates `tax_editor`/`tax_reviewer` with placeholder passwords — change them) and enrol MFA devices. |

## C. Known scope limits (documented, not defects)

Tax-modelling simplifications each needing tax-editor review are listed in
`DEVELOPER_HANDOVER.md §5`; forward-looking feature work is in §6. None
blocks go-live for the modelled scenarios — they bound *what the tool
covers*, which the editorial review and the on-screen disclosures make
explicit to the adviser.

---

**Bottom line:** the code and container are production-ready — security
hardening, isolation, audit trail, governance and health checks are in
place and tested. Go-live is gated on the Section B organisational and
infrastructure controls, which are the firm's and host's to complete and
sign off, plus a released (four-eyes-approved) rule base.
