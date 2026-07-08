"""One-shot, idempotent bootstrap so a fresh deployment can demonstrate the
whole client side WITHOUT a terminal (needed on hosts whose free tier has no
shell, e.g. Render Free). Safe to run on every boot: each step is guarded, so
after the first run it does nothing and returns immediately.

Steps, each skipped if already done:
  1. Seed + release the rule base (if no released version is in force).
  2. Create the demo firm and a demo firm-user (password from DEMO_PASSWORD,
     default "changeme-demo").
  3. Create the Emma/Sarah/Victor demo clients with generated advice.

Deliberately does NOT render PDFs (WeasyPrint is memory-heavy); the advice is
fully viewable on screen, and a PDF renders on demand when advice is generated
through the UI. Enable by setting SEED_DEMO_DATA=true; the entrypoint calls it
in the background so it never blocks startup or health checks.
"""

from __future__ import annotations

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction

DEMO_FIRM_SLUG = "demo-accountants"
DEMO_USERNAME = "demo"
TAX_YEAR = "2025/26"

# A deliberately conflicted owner-manager: what's tax-optimal is not what's
# commercially or legally clean. Engineered to make the four reviewers raise
# DIFFERENT points — wasted pension relief + annual-allowance charge (accountant),
# settlements risk on spousal dividends + gift-with-reservation (lawyer), AA
# reporting + £2m estate valuation scrutiny (HMRC), and gift affordability +
# pension lock-up + working capital (business expert) — so the panel visibly
# deliberates rather than rubber-stamps.
TENSION_FACTS = {
    "personal": {
        "other_income": 0,
        "salary_from_own_company": 0,
        "dividends_from_own_company": 70000,   # heavy extraction
        "spouse_income": 25000,                # spousal dividends -> settlements
    },
    "company": {
        "profit_before_remuneration": 90000,   # extraction is a large share -> working capital
        "employment_allowance_available": False,
        "associated_companies": 0,
    },
    "sole_trade": {"annual_profit": 0},
    "pension": {
        "threshold_income": 0,
        "adjusted_income": 0,
        "unused_aa_prior_3_years": [0, 0, 0],
        "desired_contribution": 80000,         # > earnings (unrelieved) and > AA (charge)
    },
    "estate": {
        "gross_value": 2100000,
        "liabilities": 100000,
        "home_equity_value": 500000,
        "home_passes_to_direct_descendants": True,
        "amount_to_spouse": 1500000,
        "charitable_legacy": 0,
        "combined_estate_second_death": 2000000,   # right on the £2m RNRB taper cliff
        "combined_home_equity_second_death": 600000,
        "planned_lifetime_gift": 400000,           # ~20% of the estate
        "prior_year_annual_exemption_unused": True,
    },
}


class Command(BaseCommand):
    help = "Idempotently ensure a released rule base, a demo firm/user, and demo clients with advice."

    def handle(self, *args, **options):
        from advice.generator import generate_advice
        from advice.models import ProfessionalDecision
        from advice.panel import DecisionError, deploy_panel, record_decision
        from clients.models import Client, ClientFactSet
        from clients.personas import PERSONAS
        from firms.models import Firm, User
        from ruleengine.models import RuleBaseRelease

        # 1. Rule base — only if nothing is released yet.
        if not RuleBaseRelease.objects.filter(status=RuleBaseRelease.Status.RELEASED).exists():
            self.stdout.write("No released rule base; seeding and releasing…")
            call_command("seed_rule_base", release=True)
            call_command("seed_watched_sources")
        else:
            self.stdout.write("Released rule base already in force; skipping seed.")

        # 2. Demo firm + firm-user.
        firm, _ = Firm.objects.get_or_create(
            slug=DEMO_FIRM_SLUG, defaults={"name": "Demo Accountants"}
        )
        # Partner role: partners see every client in the firm. (Staff users only
        # see clients explicitly granted to them, which would hide the demo data.)
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": "demo@example.invalid", "firm": firm, "role": User.Role.PARTNER},
        )
        changed = False
        if created:
            user.set_password(os.environ.get("DEMO_PASSWORD", "changeme-demo"))
            changed = True
            self.stdout.write(self.style.SUCCESS(f"Created demo firm-user '{DEMO_USERNAME}'."))
        if user.firm_id != firm.id:
            user.firm = firm
            changed = True
        if user.role != User.Role.PARTNER:
            # Fix an earlier demo user that was created as staff and so saw no clients.
            user.role = User.Role.PARTNER
            changed = True
            self.stdout.write(f"Promoted '{DEMO_USERNAME}' to partner so it sees all firm clients.")
        if changed:
            user.save()

        # 3. Demo clients. Per-client idempotent (only generates advice for a
        #    client that has none yet), so new demo clients are added to an
        #    existing demo firm on the next deploy.
        with connection.cursor() as c:
            c.execute("SET app.current_firm_id = %s", [str(firm.id)])

        cases = list(PERSONAS) + [
            ("D001", "Grace Okoye (review-tension case)", "individual_with_company", TENSION_FACTS),
        ]
        for reference, name, entity_type, facts in cases:
            client, _ = Client.objects.get_or_create(
                firm=firm, reference=reference,
                defaults={"name": name, "entity_type": entity_type, "created_by": user},
            )
            if client.advice_records.filter(superseded_by__isnull=True).exists():
                continue  # already seeded
            fact_set = ClientFactSet.objects.create(
                firm=firm, client=client, tax_year=TAX_YEAR,
                facts=facts, source="manual", created_by=user,
            )
            record = generate_advice(client, fact_set, user)
            note = f"{name} ({reference}): advice {record.pk}, {len(record.results)} strategies"

            # The tension case gets a full panel review and a recorded professional
            # decision, so the demo shows the four reviewers raising differing
            # points and the human resolving them — not a rubber stamp.
            if reference == "D001":
                review = deploy_panel(record, user)
                note += f"; panel: {len(review.findings)} findings, verdict '{review.verdicts['overall']}'"
                try:
                    record_decision(
                        record, user, ProfessionalDecision.Decision.NEEDS_REVISION,
                        "Panel raised commercial and disclosure concerns: the £400k gift is ~20% of "
                        "the estate (affordability), the £80k pension contribution is largely "
                        "unrelieved and triggers an annual-allowance charge, and spousal dividends "
                        "engage the settlements rules. Revise the extraction, gift and pension plan "
                        "with the client before issuing.",
                    )
                    note += "; decision recorded (needs revision)"
                except DecisionError:
                    pass
            self.stdout.write(note)

        self.stdout.write(self.style.SUCCESS("Demo clients ensured (advice on screen; PDFs render on demand)."))
