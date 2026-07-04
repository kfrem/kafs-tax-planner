"""Pension relief mechanics: relevant-UK-earnings cap (FA 2004 s.190),
relief-at-source band extension, personal allowance taper restoration, and
the employer contribution alternative. All values hand-computed from
published 2025/26 rates.
"""

import pytest

from ruleengine.calculators import combined_personal_tax, strategy_pension_carry_forward

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731


class TestReliefAtSourceMechanics:
    def test_band_extension_gives_higher_rate_relief(self):
        # Earned 60,000, gross RAS 10,000. Without: taxable 47,430 =
        # 37,700 @ 20% + 9,730 @ 40% = 11,432. With: basic limit extends to
        # 47,700, so all 47,430 @ 20% = 9,486. Saving 1,946.
        without = combined_personal_tax({"earned_income": 60000}, TAX_YEAR)
        with_ras = combined_personal_tax(
            {"earned_income": 60000, "gross_pension_contribution": 10000}, TAX_YEAR
        )
        assert without["total_tax"] == approx(11432.0)
        assert with_ras["total_tax"] == approx(9486.0)

    def test_contribution_restores_tapered_personal_allowance(self):
        # Earned 110,000: PA tapered to 7,570, tax 33,432. A 10,000 RAS
        # contribution reduces adjusted net income to 100,000, restoring the
        # full PA, and extends the bands: taxable 97,430 = 47,700 @ 20% +
        # 49,730 @ 40% = 29,432. Saving 4,000 -> with the 2,000 basic-rate
        # credit, 60% effective relief in the taper zone.
        without = combined_personal_tax({"earned_income": 110000}, TAX_YEAR)
        with_ras = combined_personal_tax(
            {"earned_income": 110000, "gross_pension_contribution": 10000}, TAX_YEAR
        )
        assert without["total_tax"] == approx(33432.0)
        assert with_ras["personal_allowance"] == approx(12570.0)
        assert with_ras["total_tax"] == approx(29432.0)


class TestPensionStrategy:
    def test_relevant_earnings_cap_applies(self):
        # Sarah's case: 40,000 desired, 28,000 relevant earnings ->
        # relievable capped at 28,000, 12,000 gets no relief. She is a
        # basic-rate taxpayer so relief is the 20% credit only: 5,600.
        result = strategy_pension_carry_forward(
            {
                "desired_contribution": 40000,
                "earned_income": 28000,
                "relevant_uk_earnings": 28000,
                "company_profit_before_remuneration": 95000,
                "unused_aa_prior_3_years": [12000, 8000, 5000],
            },
            TAX_YEAR,
        )
        personal = result["personal_route"]
        assert personal["relievable_gross"] == approx(28000.0)
        assert personal["unrelieved_amount"] == approx(12000.0)
        assert personal["basic_rate_credit_to_pension"] == approx(5600.0)
        assert personal["personal_tax_saving"] == approx(0.0)
        assert personal["total_relief_value"] == approx(5600.0)

    def test_employer_route_quantifies_ct_saving(self):
        # Employer contribution of 40,000 from 95,000 profit (marginal
        # relief band): CT falls from 21,425 to 10,825 -> saving 10,600,
        # a 26.5% marginal rate.
        result = strategy_pension_carry_forward(
            {
                "desired_contribution": 40000,
                "earned_income": 28000,
                "relevant_uk_earnings": 28000,
                "company_profit_before_remuneration": 95000,
                "unused_aa_prior_3_years": [12000, 8000, 5000],
            },
            TAX_YEAR,
        )
        employer = result["employer_route"]
        assert employer["contribution"] == approx(40000.0)
        assert employer["corporation_tax_saving"] == approx(10600.0)

    def test_minimum_3600_floor_for_non_earners(self):
        result = strategy_pension_carry_forward(
            {"desired_contribution": 5000, "earned_income": 0, "relevant_uk_earnings": 0},
            TAX_YEAR,
        )
        assert result["personal_route"]["relievable_gross"] == approx(3600.0)
        assert result["personal_route"]["unrelieved_amount"] == approx(1400.0)
        assert result["employer_route"] is None

    def test_annual_allowance_charge_basis(self):
        # 70,000 desired vs 60,000 standard AA and no carry-forward.
        result = strategy_pension_carry_forward(
            {
                "desired_contribution": 70000,
                "earned_income": 80000,
                "relevant_uk_earnings": 80000,
                "unused_aa_prior_3_years": [0, 0, 0],
            },
            TAX_YEAR,
        )
        assert result["fits_within_allowance"] is False
        assert result["amount_subject_to_annual_allowance_charge"] == approx(10000.0)
