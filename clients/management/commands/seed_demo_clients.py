"""Seeds (or refreshes) the three canonical test personas for the demo firm
and generates advice for each, so a working installation always has a
simple, a typical, and a complex client to exercise the full range.

Idempotent: existing personas get a new fact-set version (superseding the
old) only if the canonical facts changed; advice is regenerated (superseding
the previous current record) so results always reflect the current rule
base. Nothing is ever deleted — the audit chains grow, as designed.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from advice.generator import generate_advice
from clients.models import Client, ClientFactSet
from clients.personas import PERSONAS
from firms.models import Firm, User
from reports.pdf import render_advice_pdf

TAX_YEAR = "2025/26"


class Command(BaseCommand):
    help = "Seed the demo firm with the Emma/Sarah/Victor test personas and generate advice."

    def handle(self, *args, **options):
        firm = Firm.objects.get(slug="demo-accountants")
        user = User.objects.get(username="demo")
        with connection.cursor() as c:
            c.execute(f"SET app.current_firm_id = '{firm.id}'")

        with transaction.atomic():
            for reference, name, entity_type, facts in PERSONAS:
                client, _ = Client.objects.get_or_create(
                    firm=firm,
                    reference=reference,
                    defaults={"name": name, "entity_type": entity_type, "created_by": user},
                )
                current = (
                    client.fact_sets.filter(superseded_by__isnull=True, tax_year=TAX_YEAR)
                    .order_by("-created_at")
                    .first()
                )
                if current is None or current.facts != facts:
                    fact_set = ClientFactSet.objects.create(
                        firm=firm, client=client, tax_year=TAX_YEAR,
                        facts=facts, source="manual", created_by=user,
                    )
                    if current is not None:
                        current.superseded_by = fact_set
                        current.save()
                else:
                    fact_set = current

                previous = (
                    client.advice_records.filter(superseded_by__isnull=True, tax_year=TAX_YEAR)
                    .order_by("-generated_at")
                    .first()
                )
                record = generate_advice(client, fact_set, user)
                if previous is not None:
                    previous.mark_superseded(record)
                render_advice_pdf(record)
                self.stdout.write(
                    f"{name} ({reference}): advice record {record.pk}, "
                    f"{len(record.results)} strategies, rule base {record.rule_base_release.version}"
                )

        self.stdout.write(self.style.SUCCESS("Demo personas seeded."))
