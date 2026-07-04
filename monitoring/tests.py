"""Change-monitoring tests: baseline behaviour, change detection with
diffs, false-alert suppression on cosmetic changes, the editorial workflow
(notes and release requirements), and the impact link from an alert to
dependent strategies. Fetchers are stubbed — no network in tests.
"""

import pytest
from django.core.management import call_command

from authority.models import Authority
from monitoring.models import ChangeAlert, WatchedSource
from monitoring.watchers import check_source, run_all
from ruleengine.models import RuleBaseRelease

pytestmark = pytest.mark.django_db


@pytest.fixture
def source(db):
    return WatchedSource.objects.create(
        source_type=WatchedSource.SourceType.LEGISLATION,
        label="IHTA 1984 s.18",
        url="https://example.invalid/ihta/18",
    )


def fetcher_returning(text):
    return lambda url: text


class TestWatcher:
    def test_first_check_baselines_without_alert(self, source):
        alert = check_source(source, fetcher=fetcher_returning("<p>Section 18 text</p>"))
        assert alert is None
        source.refresh_from_db()
        assert source.last_fingerprint
        assert "Section 18 text" in source.last_content_snapshot

    def test_change_raises_alert_with_diff(self, source):
        check_source(source, fetcher=fetcher_returning("<p>The exemption is unlimited.</p>"))
        alert = check_source(source, fetcher=fetcher_returning("<p>The exemption is capped.</p>"))
        assert alert is not None
        assert alert.status == ChangeAlert.Status.NEW
        assert "-The exemption is unlimited." in alert.diff_excerpt
        assert "+The exemption is capped." in alert.diff_excerpt

    def test_unchanged_content_raises_nothing(self, source):
        check_source(source, fetcher=fetcher_returning("<p>Stable text</p>"))
        assert check_source(source, fetcher=fetcher_returning("<p>Stable text</p>")) is None
        assert source.alerts.count() == 0

    def test_cosmetic_markup_change_is_not_a_change(self, source):
        check_source(source, fetcher=fetcher_returning("<p class='a'>Same  text</p>"))
        alert = check_source(
            source, fetcher=fetcher_returning("<div style='x'>Same text</div>")
        )
        assert alert is None  # normalisation strips markup and whitespace

    def test_run_all_skips_failures_and_continues(self, source):
        WatchedSource.objects.create(
            source_type=WatchedSource.SourceType.OTHER,
            label="Broken",
            url="https://example.invalid/broken",
        )

        def flaky(url):
            if "broken" in url:
                raise OSError("connection refused")
            return "content"

        summary = run_all(fetcher=flaky)
        assert summary["checked"] == 1
        assert summary["baselined"] == 1
        assert len(summary["errors"]) == 1


class TestEditorialWorkflow:
    def test_resolution_requires_notes(self, source, staff_user):
        check_source(source, fetcher=fetcher_returning("a"))
        alert = check_source(source, fetcher=fetcher_returning("b"))
        with pytest.raises(ValueError, match="requires notes"):
            alert.resolve(staff_user, ChangeAlert.Status.DISMISSED, "")

    def test_actioned_requires_release(self, source, staff_user):
        check_source(source, fetcher=fetcher_returning("a"))
        alert = check_source(source, fetcher=fetcher_returning("b"))
        with pytest.raises(ValueError, match="release"):
            alert.resolve(staff_user, ChangeAlert.Status.ACTIONED, "checked source")

    def test_full_workflow(self, source, staff_user, seeded_rule_base):
        check_source(source, fetcher=fetcher_returning("a"))
        alert = check_source(source, fetcher=fetcher_returning("b"))
        alert.mark_under_review(staff_user)
        assert alert.status == ChangeAlert.Status.UNDER_REVIEW
        release = RuleBaseRelease.objects.first()
        alert.resolve(
            staff_user,
            ChangeAlert.Status.ACTIONED,
            "Verified against legislation.gov.uk; parameter updated.",
            release=release,
        )
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.ACTIONED
        assert alert.actioned_in_release == release
        assert alert.resolved_at is not None


class TestImpactAndSeeding:
    def test_seed_watched_sources_covers_authorities(self, seeded_rule_base):
        call_command("seed_watched_sources")
        uris = set(
            Authority.objects.exclude(canonical_uri="").values_list("canonical_uri", flat=True)
        )
        assert WatchedSource.objects.count() == len(uris)
        # Idempotent
        call_command("seed_watched_sources")
        assert WatchedSource.objects.count() == len(uris)

    def test_alert_lists_dependent_strategies(self, seeded_rule_base):
        call_command("seed_watched_sources")
        jones = Authority.objects.get(canonical_citation__startswith="Jones v Garnett")
        watched = jones.watched_sources.first()
        check_source(watched, fetcher=fetcher_returning("holding v1"))
        alert = check_source(watched, fetcher=fetcher_returning("holding v2"))
        codes = {s.code for s in alert.dependent_strategies()}
        assert "salary-dividend-mix" in codes
