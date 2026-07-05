"""Raises per-firm impact alerts for a rule-base release: run after a
release is approved (and typically after run_watchers-driven editorial
work lands), so firms learn which clients' current advice relied on the
changed rules."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from advice.impact import generate_impact_alerts
from ruleengine.models import RuleBaseRelease


class Command(BaseCommand):
    help = "Create impact alerts for every firm whose current advice a release touches."

    def add_arguments(self, parser):
        parser.add_argument("version", help="Rule-base release version, e.g. 2025.3")

    def handle(self, *args, **options):
        try:
            release = RuleBaseRelease.objects.get(version=options["version"])
        except RuleBaseRelease.DoesNotExist as exc:
            raise CommandError(f"No release {options['version']!r}") from exc

        # Impact analysis is a vendor-side operation across all firms;
        # advice tables are RLS-protected, so declare the bypass context
        # the way the middleware does for superusers.
        with connection.cursor() as cursor:
            cursor.execute("SET app.current_firm_id = 'ALL'")

        created = generate_impact_alerts(release)
        by_firm = {}
        for alert in created:
            by_firm.setdefault(alert.firm.name, 0)
            by_firm[alert.firm.name] += 1
        self.stdout.write(f"{len(created)} new impact alert(s) for release {release.version}.")
        for firm_name, count in sorted(by_firm.items()):
            self.stdout.write(f"  {firm_name}: {count} advice record(s) affected")
