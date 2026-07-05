"""Runs every active watcher once: fetches each watched primary source,
compares against the last fingerprint, and files ChangeAlerts into the
editorial queue. Intended to be scheduled (cron / task queue); Budget and
fiscal-event days warrant an extra manual run."""

from django.core.management.base import BaseCommand

from monitoring.watchers import run_all


class Command(BaseCommand):
    help = "Fetch all watched sources and raise change alerts into the editorial queue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebaseline",
            action="store_true",
            help="Silently re-baseline all sources instead of alerting. Use once "
            "after a fetch-strategy change, when unchanged content is merely "
            "REPRESENTED differently (e.g. HTML scrape -> XML feed).",
        )

    def handle(self, *args, **options):
        summary = run_all(rebaseline=options["rebaseline"])
        self.stdout.write(
            f"checked={summary['checked']} baselined={summary['baselined']} "
            f"alerts={summary['alerts']} errors={len(summary['errors'])}"
        )
        for error in summary["errors"]:
            self.stdout.write(self.style.WARNING(f"  fetch failed: {error}"))
        if summary["alerts"]:
            self.stdout.write(self.style.WARNING(
                f"{summary['alerts']} change(s) detected -> review at /monitoring/"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("No changes detected."))
