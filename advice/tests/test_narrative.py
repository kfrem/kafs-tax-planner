"""Narrative layer under the §8 guardrails: the deterministic drafter's
output validates cleanly, and the validator rejects fabricated numbers or
citations regardless of what produced the draft.
"""

import pytest

from advice.generator import generate_advice
from advice.models import AdviceNarrative
from advice.narrative import (
    NarrativeRejected,
    create_narrative,
    deterministic_draft,
    validate_narrative,
)
from advice.panel import deploy_panel, persona_summaries
from clients.models import Client, ClientFactSet
from clients.personas import SARAH_FACTS

TAX_YEAR = "2025/26"

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


@pytest.fixture
def record(firm, staff_user):
    client = Client.objects.create(
        firm=firm, reference="M042", name="Sarah Mitchell",
        entity_type="individual_with_company", created_by=staff_user,
    )
    fact_set = ClientFactSet.objects.create(
        firm=firm, client=client, tax_year=TAX_YEAR,
        facts=SARAH_FACTS, source="manual", created_by=staff_user,
    )
    return generate_advice(client, fact_set, staff_user)


class TestDeterministicDrafter:
    def test_draft_contains_headline_figures_and_risk_disclosure(self, record):
        text = deterministic_draft(record)
        assert "Sarah Mitchell" in text
        assert "£54,017.50" in text          # optimal-mix net
        assert "£10,600.00" in text          # employer pension CT saving
        assert "£200,000.00" in text         # transferable IHT bands
        assert "BORDERLINE" in text          # incorporation risk disclosed

    def test_draft_passes_validator_and_stores(self, record, staff_user):
        narrative = create_narrative(record, staff_user)
        assert narrative.validation_report["valid"] is True
        assert narrative.drafter == "deterministic-v1"

    def test_narrative_append_only(self, record, staff_user):
        narrative = create_narrative(record, staff_user)
        with pytest.raises(ValueError):
            narrative.save()
        with pytest.raises(ValueError):
            narrative.delete()


class TestValidator:
    def test_fabricated_number_rejected(self, record):
        report = validate_narrative(
            "We estimate you will save £99,123.45 through this planning.", record
        )
        assert report["valid"] is False
        assert any("99,123.45" in v for v in report["violations"])

    def test_fabricated_citation_rejected(self, record):
        report = validate_narrative(
            "This is supported by the Imaginary Taxes Act 2019.", record
        )
        assert report["valid"] is False
        assert any("Imaginary Taxes Act 2019" in v for v in report["violations"])

    def test_numbers_from_record_prose_are_allowed(self, record):
        # '7 years' and 'IHTA 1984' style content comes from the record's
        # own explanations and citations.
        report = validate_narrative(
            "No tax arises if you survive the gift by 7 years, per the "
            "Inheritance Tax Act 1984.",
            record,
        )
        assert report["valid"] is True

    def test_rejected_draft_cannot_be_stored(self, record, staff_user):
        def lying_llm(_record):
            return "Trust me: this saves £1,234,567 under the Fabricated Act 2030."

        before = AdviceNarrative.objects.count()
        with pytest.raises(NarrativeRejected):
            create_narrative(record, staff_user, draft_fn=lying_llm, drafter_name="llm-x")
        assert AdviceNarrative.objects.count() == before


class TestPanelVoices:
    def test_summaries_reexpress_findings_without_adding(self, record, staff_user):
        review = deploy_panel(record, staff_user)
        summaries = persona_summaries(review)
        assert {s["persona"] for s in summaries} == {
            "tax_accountant", "tax_lawyer", "hmrc_consultant", "business_expert",
        }
        # Explain-only: every point in a voice is verbatim a stored finding
        # message — nothing added, nothing dropped in severity ordering.
        stored_messages = {f["message"] for f in review.findings}
        for summary in summaries:
            for point in summary["points"]:
                assert point["message"] in stored_messages
        accountant = next(s for s in summaries if s["persona"] == "tax_accountant")
        assert accountant["verdict"] in ("clear", "attention", "blocked")
        assert accountant["lead"].startswith("The tax accountant")
