"""Release impact alerts: when a rule-base release touches parameters
behind strategies in current advice, the affected firms get an alert per
advice record — scoped by effective dating, idempotent, and firm-isolated.
"""

import datetime

import pytest
from psycopg.types.range import Range

from advice.generator import generate_advice
from advice.impact import affected_current_advice, generate_impact_alerts
from advice.models import AdviceImpactAlert
from clients.models import Client, ClientFactSet
from clients.personas import EMMA_FACTS, SARAH_FACTS
from ruleengine.models import RuleBaseRelease, TaxParameter

TAX_YEAR = "2025/26"

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


@pytest.fixture
def make_advice(firm, staff_user):
    def _make(reference, name, facts):
        client = Client.objects.create(
            firm=firm, reference=reference, name=name,
            entity_type="individual_with_company", created_by=staff_user,
        )
        fact_set = ClientFactSet.objects.create(
            firm=firm, client=client, tax_year=TAX_YEAR,
            facts=facts, source="manual", created_by=staff_user,
        )
        return generate_advice(client, fact_set, staff_user)

    return _make


def _release_changing(key, effective_from, version="2099.1"):
    """A released rule-base release re-issuing an existing parameter's
    payload (identical values: the impact machinery must react to the
    CHANGE EVENT, not to whether numbers differ)."""
    template = TaxParameter.objects.filter(key=key).order_by("-id").first()
    release = RuleBaseRelease.objects.create(
        version=version,
        changelog=f"Test release touching {key}",
        effective_date=effective_from,
        status=RuleBaseRelease.Status.RELEASED,
        editor=RuleBaseRelease.objects.first().editor,
    )
    TaxParameter.objects.create(
        key=key, label=template.label, tax_domain=template.tax_domain,
        effective_range=Range(effective_from, None, bounds="[)"),
        payload=template.payload, risk_classification=template.risk_classification,
        introduced_in_release=release,
    )
    return release


class TestImpactAnalysis:
    def test_affected_advice_found_with_strategy_overlap(self, make_advice):
        sarah = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        emma = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        release = _release_changing("income_tax.bands", datetime.date(2025, 4, 6))

        affected = dict(affected_current_advice(release))
        assert sarah in affected and emma in affected
        # Sarah's mix strategy consumes income_tax.bands; Emma's pension does.
        assert "salary-dividend-mix" in affected[sarah]
        assert "pension-annual-allowance-carry-forward" in affected[emma]

    def test_effective_dating_scopes_impact(self, make_advice):
        # A 2026/27-onward change must NOT alert 2025/26 advice.
        make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        release = _release_changing("income_tax.bands", datetime.date(2026, 4, 6))
        assert affected_current_advice(release) == []

    def test_iht_only_release_does_not_alert_emma(self, make_advice):
        # Emma has no estate: an IHT rule change is irrelevant to her.
        emma = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        release = _release_changing("iht.nil_rate_band", datetime.date(2025, 4, 6))
        assert emma not in {r for r, _ in affected_current_advice(release)}

    def test_alert_generation_is_idempotent(self, make_advice):
        make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        release = _release_changing("income_tax.bands", datetime.date(2025, 4, 6))
        first = generate_impact_alerts(release)
        second = generate_impact_alerts(release)
        assert len(first) == 1
        assert second == []
        assert AdviceImpactAlert.objects.count() == 1

    def test_superseded_advice_is_not_alerted(self, make_advice, staff_user):
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        replacement = generate_advice(record.client, record.fact_set, staff_user)
        record.mark_superseded(replacement)
        release = _release_changing("income_tax.bands", datetime.date(2025, 4, 6))
        affected_records = {r for r, _ in affected_current_advice(release)}
        assert record not in affected_records
        assert replacement in affected_records


class TestImpactWorkflow:
    def test_mark_reviewed(self, make_advice, staff_user):
        make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        release = _release_changing("income_tax.bands", datetime.date(2025, 4, 6))
        (alert,) = generate_impact_alerts(release)
        alert.mark_reviewed(staff_user, "Regenerated as advice #99; client informed.")
        alert.refresh_from_db()
        assert alert.status == "reviewed"
        assert alert.reviewed_by == staff_user
        assert alert.reviewed_at is not None
