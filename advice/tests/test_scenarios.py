"""Scenario modelling: same engine path as advice, ephemeral by design.
"""

import pytest

from advice.models import AdviceRecord
from advice.scenarios import apply_overrides, run_scenario
from clients.personas import SARAH_FACTS

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


class TestOverrides:
    def test_nested_paths_applied_without_mutating_original(self):
        modified = apply_overrides(SARAH_FACTS, {"pension.desired_contribution": 10000})
        assert modified["pension"]["desired_contribution"] == 10000
        assert SARAH_FACTS["pension"]["desired_contribution"] == 40000  # untouched
        assert modified["company"] == SARAH_FACTS["company"]  # rest carried over


class TestRunScenario:
    def test_pension_override_changes_only_what_it_should(self, db):
        # Sarah's real plan wastes £12,000 above her relevant earnings; a
        # £10,000 scenario contribution is fully relievable: 20% credit
        # 2,000, no band saving (basic-rate), no unrelieved slice.
        result = run_scenario(
            SARAH_FACTS, TAX_YEAR, {"pension.desired_contribution": 10000}
        )
        scenario_pension = next(
            r["quantification"]
            for r in result["scenario_results"]
            if r["strategy_code"] == "pension-annual-allowance-carry-forward"
        )
        assert scenario_pension["personal_route"]["relievable_gross"] == approx(10000.0)
        assert scenario_pension["personal_route"]["unrelieved_amount"] == approx(0.0)
        assert scenario_pension["personal_route"]["total_relief_value"] == approx(2000.0)

        # The salary/dividend position is untouched by a pension override.
        row = next(c for c in result["comparison"] if c["code"] == "salary-dividend-mix")
        assert row["delta"] == approx(0.0)

    def test_comparison_headline_delta(self, db):
        # Halving the planned gift halves the seven-year IHT saving:
        # 100,000 -> 50,000 gift means saving falls 40,000 -> 20,000.
        result = run_scenario(SARAH_FACTS, TAX_YEAR, {"estate.planned_lifetime_gift": 50000})
        row = next(c for c in result["comparison"] if c["code"] == "iht-lifetime-gifting-pets")
        assert row["base"] == approx(40000.0)
        assert row["scenario"] == approx(20000.0)
        assert row["delta"] == approx(-20000.0)

    def test_scenarios_store_nothing(self, db):
        before = AdviceRecord.objects.count()
        run_scenario(SARAH_FACTS, TAX_YEAR, {"company.profit_before_remuneration": 150000})
        assert AdviceRecord.objects.count() == before

    def test_base_matches_generator_output(self, db, firm, staff_user):
        from advice.generator import generate_advice
        from clients.models import Client, ClientFactSet

        client = Client.objects.create(
            firm=firm, reference="M042", name="Sarah Mitchell",
            entity_type="individual_with_company", created_by=staff_user,
        )
        fact_set = ClientFactSet.objects.create(
            firm=firm, client=client, tax_year=TAX_YEAR,
            facts=SARAH_FACTS, source="manual", created_by=staff_user,
        )
        record = generate_advice(client, fact_set, staff_user)
        result = run_scenario(SARAH_FACTS, TAX_YEAR, {"pension.desired_contribution": 10000})
        # The scenario's BASE leg is byte-identical to real advice: one
        # engine path, no divergence between scratch work and the record.
        assert result["base_results"] == record.results
