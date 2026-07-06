"""The self-audit runs on every push: real client cases (advice/audit_cases.py)
are generated, PDF-rendered, panel-reviewed and independently recomputed, and
every live strategy must be exercised. This is the standing gate that stops the
kind of end-to-end drift (e.g. an unmigrated database, an uncited or
non-reproducible figure) that unit tests alone cannot see.
"""

import pytest
from django.core.management import CommandError, call_command

from monitoring.models import WatchedSource

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


@pytest.fixture
def sources_with_snapshots(db):
    # The editorial pre-check reads the watchers' primary-source snapshots;
    # the test database has none until we seed them (mirrors test_editorial).
    call_command("seed_watched_sources")
    WatchedSource.objects.update(
        last_fingerprint="test", last_content_snapshot="source text " * 30
    )


def test_self_audit_passes_end_to_end(sources_with_snapshots, firm, staff_user, capsys):
    # The test database is built fresh from migrations, so skip the
    # unapplied-migration check (that guardrail is for the dev/prod DB).
    call_command(
        "self_audit",
        "--skip-migration-check",
        firm_slug=firm.slug,
        username=staff_user.username,
    )
    out = capsys.readouterr().out
    assert "SELF-AUDIT PASSED" in out
    assert "all 31 live strategies exercised end to end" in out


def test_self_audit_fails_loudly_on_an_uncited_strategy(firm, staff_user):
    # Break provenance: strip the authorities off a strategy the audit exercises.
    # The tax lawyer's L1 check must turn this into a hard failure — proving the
    # audit does not merely rubber-stamp.
    from ruleengine.models import Strategy

    strategy = Strategy.objects.get(code="salary-sacrifice-into-pension")
    strategy.authorities.clear()

    with pytest.raises(CommandError):
        call_command(
            "self_audit",
            "--skip-migration-check",
            firm_slug=firm.slug,
            username=staff_user.username,
        )
