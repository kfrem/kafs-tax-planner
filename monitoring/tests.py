"""Change-monitoring tests: baseline behaviour, change detection with
diffs, false-alert suppression on cosmetic changes, the editorial workflow
(notes and release requirements), and the impact link from an alert to
dependent strategies. Fetchers are stubbed — no network in tests.
"""

import pytest
from django.core.management import call_command

from authority.models import Authority
from monitoring.models import ChangeAlert, WatchedSource
from monitoring.watchers import (
    check_source,
    fetch_govuk_content,
    fetch_legislation,
    resolve_fetcher,
    run_all,
)
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


class TestFeedFetchers:
    def test_legislation_uses_xml_api_first(self):
        calls = []

        def http(url):
            calls.append(url)
            return "<akomaNtoso>Section text</akomaNtoso>"

        text = fetch_legislation("https://www.legislation.gov.uk/ukpga/1984/51/section/18", http=http)
        assert calls == ["https://www.legislation.gov.uk/ukpga/1984/51/section/18/data.xml"]
        assert "Section text" in text

    def test_legislation_falls_back_to_page_on_feed_error(self):
        def http(url):
            if url.endswith("/data.xml"):
                raise OSError("404")
            return "<html>page text</html>"

        text = fetch_legislation("https://www.legislation.gov.uk/x", http=http)
        assert "page text" in text

    def test_govuk_uses_content_api_and_extracts_details(self):
        calls = []

        def http(url):
            calls.append(url)
            return '{"details": {"body": "EIM00500 manual text"}, "links": {"ignored": true}}'

        text = fetch_govuk_content("https://www.gov.uk/hmrc-internal-manuals/employment-income-manual/eim00500", http=http)
        assert calls[0] == "https://www.gov.uk/api/content/hmrc-internal-manuals/employment-income-manual/eim00500"
        assert "EIM00500 manual text" in text
        assert "ignored" not in text  # only the substantive details payload

    def test_resolver_picks_fetcher_by_source_type(self, db):
        legislation = WatchedSource.objects.create(
            source_type=WatchedSource.SourceType.LEGISLATION,
            label="L", url="https://www.legislation.gov.uk/x",
        )
        calls = []
        resolve_fetcher(legislation, http=lambda u: calls.append(u) or "x")(legislation.url)
        assert calls[0].endswith("/data.xml")

    def test_rebaseline_suppresses_representation_change_alerts(self, source):
        check_source(source, fetcher=fetcher_returning("<html>same law, html scrape</html>"))
        # Fetch strategy changes: same law arrives as XML. Without
        # rebaseline this would false-alert; with it, silence.
        summary = run_all(
            fetcher=fetcher_returning("<xml>same law, xml feed</xml>"), rebaseline=True
        )
        assert summary["alerts"] == 0
        assert summary["baselined"] == 1
        assert source.alerts.count() == 0


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


class TestAuthorityStatusWorkflow:
    def test_change_requires_reason_and_logs_append_only(self, seeded_rule_base, staff_user):
        from authority.models import AuthorityStatusChange, record_status_change

        jones = Authority.objects.get(canonical_citation__startswith="Jones v Garnett")
        with pytest.raises(ValueError, match="requires a reason"):
            record_status_change(jones, staff_user, Authority.Status.DOUBTED, "  ")

        change = record_status_change(
            jones, staff_user, Authority.Status.DOUBTED,
            "Hypothetical UT decision doubting the s.626 exemption scope.",
        )
        jones.refresh_from_db()
        assert jones.status == Authority.Status.DOUBTED
        assert change.old_status == Authority.Status.IN_FORCE
        with pytest.raises(ValueError):
            change.save()  # append-only
        with pytest.raises(ValueError):
            change.delete()
        assert AuthorityStatusChange.objects.count() == 1

    def test_same_status_rejected(self, seeded_rule_base, staff_user):
        from authority.models import record_status_change

        jones = Authority.objects.get(canonical_citation__startswith="Jones v Garnett")
        with pytest.raises(ValueError, match="already has that status"):
            record_status_change(jones, staff_user, Authority.Status.IN_FORCE, "no-op")

    def test_status_change_raises_editorial_alert_via_view(self, seeded_rule_base, admin_client):
        call_command("seed_watched_sources")
        jones = Authority.objects.get(canonical_citation__startswith="Jones v Garnett")
        response = admin_client.post(
            f"/monitoring/authorities/{jones.pk}/status/",
            {"new_status": "overruled", "reason": "Hypothetical SC decision [2027] UKSC 1."},
        )
        assert response.status_code == 302
        jones.refresh_from_db()
        assert jones.status == Authority.Status.OVERRULED
        alert = ChangeAlert.objects.get(source__authority=jones)
        assert "overruled" in alert.diff_excerpt
        codes = {s.code for s in alert.dependent_strategies()}
        assert "salary-dividend-mix" in codes


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


def _open_alert(source):
    """Baseline then change a source so it carries exactly one open alert."""
    check_source(source, fetcher=fetcher_returning("baseline text"))
    return check_source(source, fetcher=fetcher_returning("changed text"))


class TestEditorialQueueViews:
    """The HTTP layer of the editorial queue: rendering, the resolve
    workflow driven through the form, its failure modes surfaced as
    messages rather than exceptions, and the staff-only access boundary
    (this is rule-base governance, not firm workspace)."""

    def test_queue_renders_open_alert_for_staff(self, source, admin_client):
        _open_alert(source)
        response = admin_client.get("/monitoring/")
        assert response.status_code == 200
        body = response.content.decode()
        # Header count reflects exactly the one open alert we created.
        assert "Open alerts (1)" in body
        assert source.label in body

    def test_queue_hidden_from_firm_user(self, client, staff_user):
        # A firm staff member (role STAFF, is_staff False) is not the
        # rule-base reviewer: staff_member_required must bounce them.
        assert staff_user.is_staff is False
        client.force_login(staff_user)
        response = client.get("/monitoring/")
        assert response.status_code == 302
        assert "/admin/login" in response.url

    def test_queue_redirects_anonymous(self, client):
        response = client.get("/monitoring/")
        assert response.status_code == 302
        assert "/admin/login" in response.url

    def test_authorities_page_renders_for_staff(self, seeded_rule_base, admin_client):
        response = admin_client.get("/monitoring/authorities/")
        assert response.status_code == 200
        body = response.content.decode()
        # A seeded authority and one of its dependent strategies are shown.
        assert "Jones v Garnett" in body
        assert "salary-dividend" in body.lower()

    def test_action_mark_under_review_via_view(self, source, admin_client):
        alert = _open_alert(source)
        response = admin_client.post(
            f"/monitoring/alert/{alert.pk}/action/", {"action": "under_review"}
        )
        assert response.status_code == 302
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.UNDER_REVIEW
        assert alert.reviewed_by is not None

    def test_action_dismiss_with_notes_via_view(self, source, admin_client):
        alert = _open_alert(source)
        response = admin_client.post(
            f"/monitoring/alert/{alert.pk}/action/",
            {"action": "dismissed", "notes": "Checked source: wording change only, no rule impact."},
            follow=True,
        )
        assert response.status_code == 200
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.DISMISSED
        assert alert.resolved_at is not None

    def test_action_dismiss_without_notes_is_refused_via_view(self, source, admin_client):
        # C3 failure mode through the view: the model's notes requirement
        # must surface as an error message, not a 500, and leave the alert
        # open.
        alert = _open_alert(source)
        response = admin_client.post(
            f"/monitoring/alert/{alert.pk}/action/",
            {"action": "dismissed", "notes": "   "},
            follow=True,
        )
        assert response.status_code == 200
        assert b"requires notes" in response.content
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.NEW

    def test_action_actioned_records_release_via_view(self, source, seeded_rule_base, admin_client):
        alert = _open_alert(source)
        release = RuleBaseRelease.objects.first()
        response = admin_client.post(
            f"/monitoring/alert/{alert.pk}/action/",
            {
                "action": "actioned",
                "notes": "Rate corrected under this release after checking legislation.gov.uk.",
                "release": str(release.pk),
            },
            follow=True,
        )
        assert response.status_code == 200
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.ACTIONED
        assert alert.actioned_in_release == release

    def test_action_actioned_without_release_is_refused_via_view(self, source, admin_client):
        # An actioned alert must name the release that carries the change;
        # omitting it is refused and the alert stays open.
        alert = _open_alert(source)
        response = admin_client.post(
            f"/monitoring/alert/{alert.pk}/action/",
            {"action": "actioned", "notes": "Verified, fix pending."},
            follow=True,
        )
        assert response.status_code == 200
        assert b"release" in response.content
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.NEW

    def test_alert_action_rejects_get(self, source, admin_client):
        alert = _open_alert(source)
        response = admin_client.get(f"/monitoring/alert/{alert.pk}/action/")
        assert response.status_code == 405

    def test_alert_action_hidden_from_firm_user(self, source, client, staff_user):
        alert = _open_alert(source)
        client.force_login(staff_user)
        response = client.post(
            f"/monitoring/alert/{alert.pk}/action/", {"action": "under_review"}
        )
        assert response.status_code == 302
        assert "/admin/login" in response.url
        alert.refresh_from_db()
        assert alert.status == ChangeAlert.Status.NEW
