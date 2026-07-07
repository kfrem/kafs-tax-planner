"""Editorial pre-check invariant: the machine review that runs before the
human tax editor's sign-off must pass with ZERO failures on the seeded
rule base (with primary-source snapshots on file). Any future parameter,
strategy, or authority added without full wiring — calculator, adapter,
golden coverage, citations, fetchable source — fails this test and
therefore fails CI, so nothing unreviewable can accumulate silently.
"""

import pytest
from django.core.management import call_command

from monitoring.models import WatchedSource
from ruleengine.editorial import precheck

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


@pytest.fixture
def sources_with_snapshots(db):
    call_command("seed_watched_sources")
    WatchedSource.objects.update(
        last_fingerprint="test", last_content_snapshot="source text " * 30
    )


class TestEditorialPrecheck:
    def test_seeded_rule_base_is_fully_wired(self, sources_with_snapshots):
        report = precheck()
        failures = []
        for section in ("parameters", "strategies", "authorities"):
            for item in report[section]:
                for name, ok, detail in item["checks"]:
                    if not ok:
                        label = item.get("key") or item.get("code") or item.get("citation")
                        failures.append(f"{label}: {name} ({detail})")
        assert failures == []
        assert report["failures"] == 0

    def test_structure_covers_all_content(self, sources_with_snapshots):
        report = precheck()
        assert len(report["parameters"]) >= 15   # every current-year parameter
        assert len(report["strategies"]) == 38   # all strategies reviewed
        assert len(report["authorities"]) >= 25  # entire registry reviewed
