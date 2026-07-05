# Deployment

The app ships as a standard Docker container (zero lock-in: the same
image runs on any host). CI builds the image on every push, so a broken
Dockerfile cannot reach `main`.

## Run the full stack anywhere with Docker

```bash
docker compose up --build
docker compose exec app python manage.py seed_rule_base   # DRAFT; reviewer releases in /admin/
docker compose exec app python manage.py seed_watched_sources
# -> http://localhost:8000
```

The compose file provisions PostgreSQL 16 with the **non-superuser
`app_user` role** automatically (row-level security is only real if the
app does not connect as a superuser). The app container waits for the
database, applies migrations, then serves via gunicorn with WhiteNoise
for static files.

Required environment for any host:

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgres://app_user:…@host:5432/taxplanner` — non-superuser role |
| `SECRET_KEY` | generate per environment; never reuse the dev value |
| `DEBUG` | `false` in anything shared |
| `ALLOWED_HOSTS` | the public hostname |

Scheduled job to configure on the host: `python manage.py run_watchers`
(daily; plus a manual run on Budget/fiscal-event days).

## Choosing a host (architecture doc §3)

The binding requirement is **client financial data residency that a
small firm's due-diligence checklist accepts** — in practice, a UK
region — plus managed PostgreSQL with tested backups and an Art. 28
processor agreement from the provider.

| Host | UK region | Managed Postgres | Indicative cost (MVP) | Verdict |
|---|---|---|---|---|
| Fly.io | Yes (`lhr`, London) | Via managed partners / fly postgres | ~£10–40/mo | Good first choice; container-native |
| Railway | EU (Amsterdam); UK not guaranteed | Yes | ~£15–40/mo | Fine for staging; check region for production |
| Render | EU (Frankfurt); no UK region | Yes | ~£15–50/mo | Same caveat |
| Azure UK South / AWS eu-west-2 (London) | Yes | Yes (flexible server / RDS) | ~£40–100/mo | Where firms' checklists point; move here as revenue justifies |
| Eyevinn Open Source Cloud (osaas.io) | EU (Sweden) | Community services | ~€15/mo | Nothing to gain: our stack is already 100% open source, and EU-only residency is a harder due-diligence conversation than a UK region at the same price. Its "same container anywhere" philosophy is exactly why this Dockerfile exists. |

UK GDPR does not strictly mandate UK residency (the EU holds adequacy),
but UK-region hosting removes the international-transfer analysis from
every sales conversation — the architecture doc's reasoning, unchanged.

Before real client data goes on ANY host: the §7 checklist (DPIA, Cyber
Essentials, backups with tested restores, MFA, incident-response
procedure, processor agreement) — see DEVELOPER_HANDOVER.md §6.

## Windows note

gunicorn does not run on native Windows; it exists in the container
only. Local Windows development keeps using `manage.py runserver` and
the winget GTK3 runtime for WeasyPrint, exactly as in README.
