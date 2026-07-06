# Hosting, costs, and the stack decision log

Plain-English record of the hosting/cost thinking so nobody has to rehash
it. Covers what the stack costs at each growth stage, what every component
is (including the database-as-a-service options), how easy it is to switch
provider, and a dated log of what has been decided vs what is still open.

Last updated: 6 July 2026. **Costs are indicative** (GBP, ex VAT) — always
check current pricing; hosts run frequent promotions and renewal rates
differ from intro rates.

---

## 1. The one thing to understand first

This is a **low-traffic B2B tool**, not a consumer app. Each accounting
firm has a handful of staff who generate advice occasionally (a few times
per client per year). So cost scales with the *number of firms*, but very
slowly, because the load per firm is tiny. A small server serves many firms
for a long time. **Infrastructure will not be the constraint — sales will.**

## 2. What's in the stack (and where money goes)

Hosting the app means placing two things — the **app** (compute) and the
**database** (PostgreSQL, holding client data) — plus a few small extras.

- **App compute** — where the Django Docker container runs.
- **PostgreSQL** — the database. Options:
  - the *host's own* managed Postgres (Railway / DigitalOcean / Hostinger /
    Azure / AWS) — simplest, one vendor, one bill;
  - **Neon** — serverless Postgres that scales to zero when idle; genuinely
    cheap for low traffic; generous free tier, paid from ~£15/mo; EU region;
  - **Supabase** — managed Postgres *plus* its own auth/storage/APIs. Free
    tier ~500MB but pauses when idle; paid ~£20/mo; London region. Slightly
    overkill here — the app already does its own auth and row-level
    security, so Supabase's headline extras would sit unused. Fine, but you
    pay for parts you don't need.
  - **Steer:** demo → host's built-in Postgres or a Neon free tier; real
    clients → a proper managed Postgres with automated, *tested* backups
    (from the host is simplest, Neon if you want it cheap and separate).
- **Domain** — ~£10/yr.
- **HTTPS/TLS** — free (Let's Encrypt / host-provided).
- **Transactional email** (password resets, alerts) — free tier to start
  (Postmark / Amazon SES / Resend); a paid tier (~£12/mo) only if volume
  ever grows, which for this app it barely does.
- **Error monitoring** — Sentry free tier.
- **Backups** — often included with managed Postgres, or a small add-on.

## 3. Cost by growth stage

| Component | Demo (dummy data) | 2–5 firms (real data) | 10+ firms |
|---|---|---|---|
| App compute | £3–5 | £5–12 | £15–40 |
| PostgreSQL | included / £0–5 | £8–15 | £15–50 |
| Domain | ~£1 (£10/yr) | ~£1 | ~£1 |
| Email | free | free | £0–15 |
| Monitoring | free | free | free |
| Backups | £0–1 | £1–3 | £3–10 |
| **Realistic total / month** | **£5–10** | **£10–30** | **£30–100** |

Even at 10+ firms you are likely under £100/month (nearer £30 self-managed
on a VPS). Against firm subscriptions of tens to low hundreds of pounds each
per month, hosting is a rounding error.

**Typical host choice per stage:**

- **Demo:** Railway Hobby (~£5/mo, EU) or Hostinger VPS KVM 1 (~£5/mo,
  EU/UK, Docker-template friendly). No compliance needed — dummy data only.
- **2–5 firms:** DigitalOcean App Platform (London) with managed Postgres
  (~£15–25/mo), or Hostinger VPS KVM 2 UK + backups (~£8–12/mo,
  self-managed). UK region + the compliance pack now apply.
- **10+ firms:** DigitalOcean Professional / Fly.io with a larger DB and
  daily backups (~£40–70/mo), or Azure UK South / AWS London with high
  availability where big firms' due-diligence checklists point
  (~£60–150/mo).

## 4. Switching provider as you grow — easy by design

Deliberate zero-lock-in architecture (see the `Dockerfile` header). A host
migration is low-risk because:

1. The app is **one Docker image** — runs identically anywhere; moving
   compute = deploy the same image elsewhere.
2. The database is **standard PostgreSQL** — `pg_dump` on the old,
   `pg_restore` on the new. A small DB moves in minutes.
3. **No proprietary dependencies** — no serverless functions, no
   vendor-locked auth, no host-specific APIs. Nothing to rewrite.

**Migration = ** spin up the new host → restore the DB dump → repoint the
domain's DNS → update a few environment variables. Realistically a
**half-day with a short maintenance window**. Natural path:
`Demo (Railway/Hostinger EU)` → `2–5 firms (DigitalOcean London / Hostinger UK)`
→ `10+ (DO Pro or Azure/AWS UK)`.

## 5. Decision log (what's decided vs open)

| Date | Decided / discussed | Status |
|---|---|---|
| 6 Jul 2026 | Data residency: EU is acceptable to the founder for now; UK preferred once real client data is on. | Agreed |
| 6 Jul 2026 | Demo stage will use a ~£5/mo option — **Railway Hobby** or a **Hostinger VPS** (founder already uses Hostinger). Leaning Hostinger VPS for value + one-vendor consolidation; Railway if zero server-maintenance is preferred. | **Open — pick one** |
| 6 Jul 2026 | Database for demo: host's built-in Postgres (or Neon free tier). Supabase considered but not needed (extras unused). | Agreed direction |
| 6 Jul 2026 | Real-client hosting target: DigitalOcean London (or Azure UK) with managed Postgres + tested backups, moving there when the first firm signs. | Agreed direction |
| 6 Jul 2026 | Switching hosts as size grows is accepted as easy (Docker image + pg_dump/restore); no premature over-investment in enterprise hosting. | Agreed |

**Next action for the founder:** choose the demo host (Hostinger VPS vs
Railway). Once chosen, the developer writes the one-page deploy guide for
that host and the row above moves to *Agreed*. Update this log whenever a
choice is made, so the reasoning is never re-litigated.

## 6. What we are NOT spending on (deliberately)

To keep burn near zero until revenue justifies it: no Kubernetes, no
multi-region, no paid monitoring/APM, no enterprise database HA, no CDN, no
managed-auth product. All are easy to add later and none are needed at
demo or single-digit-firm scale.
