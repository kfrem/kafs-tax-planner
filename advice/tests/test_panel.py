"""Expert panel tests: the four reviewer personas, verdict aggregation,
blocker detection (rule drift, overruled authority), and the decision
workflow gating (no decision without a panel review; no silent approval
over blockers).
"""

import pytest

from advice.generator import generate_advice
from advice.models import PanelReview, ProfessionalDecision
from advice.panel import DecisionError, deploy_panel, record_decision
from authority.models import Authority
from clients.models import Client, ClientFactSet
from clients.personas import EMMA_FACTS, SARAH_FACTS, VICTOR_FACTS
from ruleengine.models import TaxParameter

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


def _codes(review):
    return {f["code"] for f in review.findings}


class TestPanelVerdicts:
    def test_simple_client_is_clear(self, make_advice, staff_user):
        # Emma: nothing to warn about — the panel must not manufacture
        # concerns on a clean, simple case.
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        review = deploy_panel(record, staff_user)
        assert review.verdicts["overall"] == "clear"
        assert all(f["severity"] == "info" for f in review.findings)
        assert "A1_RECOMPUTED_OK" in _codes(review)

    def test_typical_client_gets_attention_items(self, make_advice, staff_user):
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        review = deploy_panel(record, staff_user)
        assert review.verdicts["overall"] == "attention"
        codes = _codes(review)
        # The panel must catch: salary below LEL (HMRC consultant), the
        # NI-year price (business expert), unrelieved pension contribution
        # (accountant), gift-with-reservation formality (lawyer), and the
        # borderline incorporation disclosure duty (lawyer).
        assert "H1_BELOW_LEL" in codes
        assert "B4_NI_YEAR_PRICE" in codes
        assert "A3_UNRELIEVED_CONTRIBUTION" in codes
        assert "L7_GWR" in codes
        assert "L3_RISK_DISCLOSURE" in codes

    def test_complex_client_taper_findings(self, make_advice, staff_user):
        record = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        review = deploy_panel(record, staff_user)
        assert review.verdicts["overall"] == "attention"
        codes = _codes(review)
        assert "A4_AA_CHARGE_EXPOSURE" in codes  # accountant: 15k over AA
        assert "H5_AA_REPORTING" in codes        # HMRC: charge must be returned
        assert "B3_GIFT_AFFORDABILITY" in codes  # business: 500k = 11% of estate

    def test_per_persona_verdicts_reported(self, make_advice, staff_user):
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        review = deploy_panel(record, staff_user)
        assert set(review.verdicts) == {
            "tax_accountant", "tax_lawyer", "hmrc_consultant", "business_expert", "overall",
        }


class TestPanelBlockers:
    def test_rule_drift_blocks_approval(self, make_advice, staff_user):
        # Advice generated, then the rule base moves (here: PA changed).
        # The accountant's independent recomputation must catch it.
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        pa = TaxParameter.objects.filter(key="income_tax.personal_allowance").order_by("-id").first()
        pa.payload = {**pa.payload, "amount": 13000}
        pa.save()

        review = deploy_panel(record, staff_user)
        assert review.verdicts["overall"] == "blocked"
        assert "A1_NOT_REPRODUCIBLE" in _codes(review)
        assert review.blockers

    def test_overruled_authority_blocks(self, make_advice, staff_user):
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        Authority.objects.filter(
            canonical_citation__startswith="Jones v Garnett"
        ).update(status=Authority.Status.OVERRULED)

        review = deploy_panel(record, staff_user)
        assert review.verdicts["overall"] == "blocked"
        assert "L2_AUTHORITY_OVERRULED" in _codes(review)


class TestDecisionWorkflow:
    def test_no_decision_without_panel_review(self, make_advice, staff_user):
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        with pytest.raises(DecisionError, match="Deploy the panel first"):
            record_decision(record, staff_user, ProfessionalDecision.Decision.APPROVED)

    def test_clean_review_can_be_approved(self, make_advice, staff_user):
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        deploy_panel(record, staff_user)
        decision = record_decision(record, staff_user, ProfessionalDecision.Decision.APPROVED)
        assert decision.pk is not None
        assert record.latest_decision.decision == "approved"

    def test_blocker_requires_override_note_to_approve(self, make_advice, staff_user):
        record = make_advice("M042", "Sarah Mitchell", SARAH_FACTS)
        pa = TaxParameter.objects.filter(key="income_tax.personal_allowance").order_by("-id").first()
        pa.payload = {**pa.payload, "amount": 13000}
        pa.save()
        deploy_panel(record, staff_user)

        with pytest.raises(DecisionError, match="override note"):
            record_decision(record, staff_user, ProfessionalDecision.Decision.APPROVED)
        decision = record_decision(
            record, staff_user, ProfessionalDecision.Decision.APPROVED,
            notes="Reviewed manually against the new PA; figures verified by hand.",
        )
        assert decision.decision == "approved"

    def test_reject_and_revise_require_notes(self, make_advice, staff_user):
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        deploy_panel(record, staff_user)
        with pytest.raises(DecisionError, match="requires a note"):
            record_decision(record, staff_user, ProfessionalDecision.Decision.REJECTED)
        decision = record_decision(
            record, staff_user, ProfessionalDecision.Decision.NEEDS_REVISION,
            notes="Client mentioned a second property — facts incomplete.",
        )
        assert decision.decision == "needs_revision"


class TestPanelImmutability:
    def test_review_append_only(self, make_advice, staff_user):
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        review = deploy_panel(record, staff_user)
        with pytest.raises(ValueError):
            review.save()
        with pytest.raises(ValueError):
            review.delete()

    def test_redeploy_creates_new_review(self, make_advice, staff_user):
        record = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        first = deploy_panel(record, staff_user)
        second = deploy_panel(record, staff_user)
        assert first.pk != second.pk
        assert PanelReview.objects.filter(advice_record=record).count() == 2
        assert record.latest_panel_review.pk == second.pk
