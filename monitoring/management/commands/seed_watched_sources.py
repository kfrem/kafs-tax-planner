"""Creates a WatchedSource for every authority record's canonical URI.
Idempotent: existing sources are kept (their baselines and alert history
are evidence), new authorities gain a watcher."""

from django.core.management.base import BaseCommand

from authority.models import Authority
from monitoring.models import WatchedSource


def source_type_for(authority: Authority) -> str:
    if authority.authority_type in (
        Authority.AuthorityType.TRIBUNAL_DECISION,
        Authority.AuthorityType.COURT_JUDGMENT,
    ):
        return WatchedSource.SourceType.CASE_LAW
    if authority.authority_type == Authority.AuthorityType.HMRC_MANUAL:
        return WatchedSource.SourceType.HMRC_MANUAL
    if "legislation.gov.uk" in (authority.canonical_uri or ""):
        return WatchedSource.SourceType.LEGISLATION
    return WatchedSource.SourceType.OTHER


class Command(BaseCommand):
    help = "Create watched sources for every authority with a canonical URI."

    def handle(self, *args, **options):
        created = 0
        for authority in Authority.objects.exclude(canonical_uri=""):
            _, was_created = WatchedSource.objects.get_or_create(
                url=authority.canonical_uri,
                defaults={
                    "authority": authority,
                    "source_type": source_type_for(authority),
                    "label": authority.canonical_citation,
                },
            )
            created += was_created
        total = WatchedSource.objects.count()
        self.stdout.write(self.style.SUCCESS(f"{created} sources created ({total} total watched)."))
