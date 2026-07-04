"""Regression tests for cross-income interaction: the gap found when running
the Sarah Mitchell scenario (sole-trade income filling the basic-rate band
and dividends triggering the personal allowance taper were being ignored by
the strategy calculators). All expected values hand-computed from published
2025/26 rates.
"""

import pytest

from ruleengine.calculators import (
    combined_personal_tax,
    strategy_incorporation_vs_sole_trade,
    strategy_salary_dividend_mix,
)

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731


class TestCombinedPersonalTax:
    def test_earned_only_matches_single_calculator(self):
        # 130,000 earned: PA fully tapered, tax 44,703 (same as the
        # income_tax_on_earned_income golden case)
        result = combined_personal_tax({"earned_income": 130000, "dividend_income": 0}, TAX_YEAR)
        assert result["personal_allowance"] == 0
        assert result["total_tax"] == approx(44703.0)

    def test_unused_personal_allowance_shelters_dividends(self):
        # Earned 9,100 leaves 3,470 of PA for dividends of 14,810.85:
        # taxable dividends 11,340.85, all basic band, less 500 allowance
        # at 8.75% -> (11,340.85 * 0.0875) - 43.75 = 948.57
        result = combined_personal_tax(
            {"earned_income": 9100, "dividend_income": 14810.85}, TAX_YEAR
        )
        assert result["taxable_earned"] == 0
        assert result["dividend_tax_due"] == approx(948.57)

    def test_dividends_trigger_personal_allowance_taper(self):
        # 28,000 earned + 73,575 dividends = 101,575 total income.
        # PA reduced by (1,575 * 0.5) = 787.50 -> 11,782.50.
        result = combined_personal_tax(
            {"earned_income": 28000, "dividend_income": 73575}, TAX_YEAR
        )
        assert result["personal_allowance"] == approx(11782.50)
        assert result["earned_tax"] == approx(3243.50)
        assert result["dividend_tax_due"] == approx(19417.19)
        assert result["total_tax"] == approx(22660.69)

    def test_no_taper_case_matches_prior_behaviour(self):
        # 12,570 salary + 63,501.46 dividends = 76,071 total, no taper:
        # must equal the pre-interaction figure of 11,962.99.
        result = combined_personal_tax(
            {"earned_income": 12570, "dividend_income": 63501.46}, TAX_YEAR
        )
        assert result["earned_tax"] == 0
        assert result["dividend_tax_due"] == approx(11962.99)


class TestSalaryDividendMixWithOtherIncome:
    """The Sarah Mitchell scenario: £95,000 company profit with £28,000 of
    sole-trade income alongside. With the interaction modelled, low/no salary
    beats the £12,570 salary that wins when other income is ignored, because
    extra salary pushes total income further into the PA taper."""

    def test_sarah_scenario_full_numbers(self):
        # Explicit salary_options pins the fixed-grid path; the optimiser
        # path is covered separately in TestSalaryOptimiser.
        result = strategy_salary_dividend_mix(
            {
                "company_profit_before_remuneration": 95000,
                "other_personal_income": 28000,
                "employment_allowance_available": False,
                "salary_options": [0, 6500, 9100, 12570, 50270],
            },
            TAX_YEAR,
        )
        by_salary = {c["salary"]: c for c in result["comparisons"]}

        # salary 0: CT 21,425; dividends 73,575; incremental personal tax
        # = 22,660.69 (taper case above) - 3,086 (tax on 28,000 alone)
        # = 19,574.69; net = 73,575 - 19,574.69 = 54,000.31
        assert by_salary[0]["corporation_tax"] == approx(21425.0)
        assert by_salary[0]["personal_tax_on_extraction"] == approx(19574.69)
        assert by_salary[0]["net_to_individual"] == approx(54000.31)

        # salary 12,570: employer NIC 1,135.50; CT 17,793.04; dividends
        # 63,501.46; total income 104,071.46 tapers PA to 10,534.27;
        # personal tax 25,479.08 - 3,086 = 22,393.08;
        # net = 12,570 + 63,501.46 - 22,393.08 = 53,678.38
        assert by_salary[12570]["employer_nic"] == approx(1135.50)
        assert by_salary[12570]["personal_tax_on_extraction"] == approx(22393.08)
        assert by_salary[12570]["net_to_individual"] == approx(53678.38)

        # With other income modelled, zero salary now wins.
        assert result["recommended"]["salary"] == 0

    def test_without_other_income_recommendation_unchanged(self):
        # Sanity: with no other income the pre-interaction recommendation
        # (12,570 salary) still holds — and the optimiser confirms it is the
        # true optimum, not just the best of a fixed grid: below the primary
        # threshold each extra £1 of salary nets ~+44p, above it ~-9p, so
        # the maximum sits exactly at 12,570.
        result = strategy_salary_dividend_mix(
            {"company_profit_before_remuneration": 95000, "other_personal_income": 0},
            TAX_YEAR,
        )
        assert result["salary_optimised_to_nearest_pound"] is True
        assert result["recommended"]["salary"] == 12570
        assert result["recommended"]["net_to_individual"] == approx(64108.47)


class TestSalaryOptimiser:
    def test_finds_interior_optimum_grid_misses(self):
        # Sarah's case again, optimised. The fixed grid recommended salary 0
        # (net 54,000.31). The true optimum is the £5,000 employer NIC
        # secondary threshold: below it salary costs no NIC, and with her
        # sole-trade income using the PA, each £1 of salary up to 5,000
        # nets slightly more than the top-sliced dividend it displaces.
        # Hand-computed at 5,000: CT 20,100 on taxable profit 90,000;
        # dividends 69,900; personal tax 23,968.50 - 3,086 = 20,882.50;
        # net = 5,000 + 69,900 - 20,882.50 = 54,017.50.
        result = strategy_salary_dividend_mix(
            {"company_profit_before_remuneration": 95000, "other_personal_income": 28000},
            TAX_YEAR,
        )
        best = result["recommended"]
        assert best["salary"] == 5000
        assert best["net_to_individual"] == approx(54017.50)
        # And it must beat every reference-grid point.
        assert all(
            best["net_to_individual"] >= c["net_to_individual"]
            for c in result["comparisons"]
        )

    def test_respects_company_affordability(self):
        # The optimiser must never recommend a salary whose employer NIC
        # the company cannot fund from profit (caught in review: the first
        # scan implementation happily paid 95,000 salary from 95,000 profit
        # with 13,500 NIC from nowhere). At 10,000 profit the max feasible
        # salary is 9,347: 9,347 + 15% NIC on (9,347 - 5,000) = 9,999.05.
        result = strategy_salary_dividend_mix(
            {"company_profit_before_remuneration": 10000, "other_personal_income": 0},
            TAX_YEAR,
        )
        best = result["recommended"]
        assert best["salary"] == 9347
        assert best["salary"] + best["employer_nic"] <= 10000

    def test_reference_comparisons_include_thresholds_and_optimum(self):
        result = strategy_salary_dividend_mix(
            {"company_profit_before_remuneration": 95000, "other_personal_income": 28000},
            TAX_YEAR,
        )
        salaries = [c["salary"] for c in result["comparisons"]]
        # NIC secondary threshold, primary threshold, UEL, zero — plus the
        # optimum (5,000 coincides with the secondary threshold here).
        assert 0 in salaries and 5000 in salaries and 12570 in salaries and 50270 in salaries


class TestIncorporationWithOtherIncome:
    def test_sole_trader_arm_is_incremental(self):
        # 28,000 sole-trade profit on its own: IT 3,086 + Class 4 925.80.
        result = strategy_incorporation_vs_sole_trade(
            {"annual_profit": 28000, "other_personal_income": 0}, TAX_YEAR
        )
        assert result["sole_trader"]["income_tax"] == approx(3086.0)
        assert result["sole_trader"]["class4_nic"] == approx(925.80)
        assert result["recommendation"] == "remain_sole_trader"

    def test_other_income_pushes_profit_into_higher_rate(self):
        # With 45,000 of other income, the 28,000 profit is taxed mostly at
        # 40%: baseline tax(45,000) = 6,486; tax(73,000) = 16,632
        # (taxable 60,430 = 37,700 @ 20% + 22,730 @ 40%); incremental 10,146.
        result = strategy_incorporation_vs_sole_trade(
            {"annual_profit": 28000, "other_personal_income": 45000}, TAX_YEAR
        )
        assert result["sole_trader"]["income_tax"] == approx(10146.0)
