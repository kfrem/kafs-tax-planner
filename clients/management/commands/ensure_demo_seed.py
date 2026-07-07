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


class Command(BaseCommand):
    help = "Idempotently ensure a released rule base, a demo firm/user, and demo clients with advice."

    def handle(self, *args, **options):
        from advice.generator import generate_advice
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
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": "demo@example.invalid", "firm": firm, "role": User.Role.STAFF},
        )
        if created:
            user.set_password(os.environ.get("DEMO_PASSWORD", "changeme-demo"))
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo firm-user '{DEMO_USERNAME}'."))
        elif user.firm_id != firm.id:
            user.firm = firm
            user.save()

        # 3. Demo clients — only if this firm has none yet.
        with connection.cursor() as c:
            c.execute("SET app.current_firm_id = %s", [str(firm.id)])

        if Client.objects.filter(firm=firm).exists():
            self.stdout.write("Demo clients already present; nothing to do.")
            return

        with transaction.atomic():
            for reference, name, entity_type, facts in PERSONAS:
                client, _ = Client.objects.get_or_create(
                    firm=firm,
                    reference=reference,
                    defaults={"name": name, "entity_type": entity_type, "created_by": user},
                )
                fact_set = ClientFactSet.objects.create(
                    firm=firm, client=client, tax_year=TAX_YEAR,
                    facts=facts, source="manual", created_by=user,
                )
                record = generate_advice(client, fact_set, user)
                self.stdout.write(
                    f"{name} ({reference}): advice {record.pk}, {len(record.results)} strategies."
                )
        self.stdout.write(self.style.SUCCESS("Demo clients seeded (advice on screen; PDFs render on demand)."))
