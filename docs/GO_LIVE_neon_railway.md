# Go-live runbook — Neon (database) + Railway (app)

A live **test** deployment: the app on Railway, its PostgreSQL on Neon. Follow the
steps in order. The repo side is already done (see §0); the rest are dashboard
actions only you can do, because they need your accounts. **Do not paste any
password, connection string or token into the chat** — set them in the Railway
dashboard yourself.

> **Data-residency caveat — read first.** This is a live *test* with **test/demo
> data only**. Do **not** enter real client data until the
> [`PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md) §7 checklist is done (DPIA,
> processor agreement, backups with tested restores, Cyber Essentials). For that
> production step, host the database in a **UK/London region**; for this test an
> EU region is fine.

---

## 0. Already done in the repo (no action needed)

- `Dockerfile` + `docker/entrypoint.sh` — builds the image, waits for the DB,
  runs migrations, then serves via gunicorn + WhiteNoise. **Validated to build
  locally.**
- `railway.json` — tells Railway to build the Dockerfile and health-check `/healthz`.
- `config/settings.py` — now handles a PaaS reverse proxy correctly:
  `SECURE_PROXY_SSL_HEADER` (prevents the HTTPS redirect loop), and it
  auto-trusts Railway's generated domain in both `ALLOWED_HOSTS` and
  `CSRF_TRUSTED_ORIGINS`. Row-Level Security uses `FORCE ROW LEVEL SECURITY`, so
  tenant isolation holds on Neon (Neon never grants Postgres superuser).

## 1. Neon — create the database (~3 min)

1. Sign in at **neon.tech** (GitHub sign-in is fine).
2. **Create project.** Name it e.g. `kafs-tax-planner`. Region: **AWS Europe
   (London) `eu-west-2`** if offered, otherwise **Frankfurt `eu-central-1`**.
3. Database name: `taxplanner` (or accept the default and note it).
4. Open **Connection Details** and copy the connection string. **Use the DIRECT
   (non-pooled) string** — i.e. the host **without** `-pooler` in it — for now;
   it avoids a known prepared-statement clash between psycopg3 and Neon's
   PgBouncer pooler. It looks like:
   ```
   postgresql://<user>:<password>@ep-xxxx.eu-west-2.aws.neon.tech/taxplanner?sslmode=require
   ```
   Keep it handy for step 2 (paste it into Railway, not here).

## 2. Railway — create and configure the app (~5 min)

1. Sign in at **railway.com** with **GitHub**, and authorise access to the
   `kfrem/kafs-tax-planner` repo.
2. **New Project → Deploy from GitHub repo →** pick `kfrem/kafs-tax-planner`.
   Railway reads `railway.json` and starts a Dockerfile build. Let the first
   build run (it may fail the health check until you add the variables below —
   that's expected).
3. **Generate a public domain:** service → **Settings → Networking → Generate
   Domain**. This creates `something.up.railway.app` and sets the
   `RAILWAY_PUBLIC_DOMAIN` variable the app reads automatically.
4. **Variables** tab → add:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | *(paste the Neon DIRECT string from step 1.4)* |
   | `SECRET_KEY` | a fresh 64-char random — generate with the command below |
   | `DEBUG` | `False` |

   Generate a SECRET_KEY locally and paste it straight into Railway:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
   `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are handled automatically from the
   generated domain — you only need to set them if you later add a custom domain.
5. Railway redeploys on save. Watch **Deployments → logs**: you should see
   `Applying database migrations…`, then gunicorn boot, then the health check at
   `/healthz` go green.

## 3. First-run data (one-off, in a Railway shell) (~3 min)

Open a shell on the service (Railway: the service's **⋮ → "Run a command"**, or
`railway run` from the Railway CLI). Run:

```bash
python manage.py seed_rule_base --release   # test/live: releases the rule base so advice can generate
python manage.py seed_watched_sources       # registers the legislation watchers
python manage.py createsuperuser            # your admin login
```

- `--release` is the quick path for this **test**. For real advice to clients,
  seed **without** `--release` and instead mark the `RuleBaseRelease` as
  *Released* in `/admin/` with a **second reviewer** (the four-eyes governance).
- Optional demo data to click through: `python manage.py seed_demo_clients`.

## 4. Log in and smoke-test

1. Visit `https://<your-domain>.up.railway.app/` → you should get the login page.
2. Log in as the superuser. The app uses MFA (django-otp); follow the prompt to
   enrol an authenticator on first login (or manage devices in `/admin/`).
3. Generate advice for a demo client and download the PDF — confirms the whole
   pipeline (rules → calculators → panel → WeasyPrint) works on the live stack.
4. `GET /healthz` should return `{"status":"ok"}`.

## 5. Optional: daily legislation watcher

Add a Railway **cron** (service → Settings → Cron Schedule, or a separate
service) running daily:
```bash
python manage.py run_watchers
```
Plus a manual run on Budget / fiscal-event days. Not required for the test.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Redirect loop / "too many redirects" | Proxy TLS header — already fixed via `SECURE_PROXY_SSL_HEADER`; make sure `DEBUG=False` is set so the security block is active. |
| `DisallowedHost` in logs | The domain isn't in `ALLOWED_HOSTS`. Confirm **Generate Domain** was done (sets `RAILWAY_PUBLIC_DOMAIN`); for a custom domain add it to an `ALLOWED_HOSTS` variable. |
| CSRF "origin checking failed" on login | Add `https://<domain>` to a `CSRF_TRUSTED_ORIGINS` variable (auto-set for the Railway domain; needed for custom domains). |
| Health check never turns green | The app can't reach Neon. Re-check `DATABASE_URL`, that it ends with `?sslmode=require`, and that you used the **direct** (non-`-pooler`) host. |
| `prepared statement "…" already exists` | You used the Neon **pooled** endpoint. Switch `DATABASE_URL` to the direct host. |
| "No released TaxParameter…" when generating advice | The rule base isn't released. Run `seed_rule_base --release` (test) or release in `/admin/` (production). |

## What I (Claude) can and cannot do here

- **Done for you:** all repo/config changes, local Docker-build validation, this runbook.
- **Your part:** the account/dashboard steps above — they need your Neon and
  Railway logins. I will **never** ask for or handle your passwords, connection
  strings or tokens.
- **I can help next:** paste me a build/deploy **log** (with secrets redacted)
  and I'll diagnose it; or when you're back, we continue with Milestone 2.
