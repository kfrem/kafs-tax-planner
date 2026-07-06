"""Tier-1 planning strategies (see docs/TAX_PLANNING_COVERAGE.md). All
expected values hand-computed from published 2025/26 rates, with the working
shown in the comment."""

import pytest

from ruleengine.calculators import (
    strategy_capital_allowances,
    strategy_cgt_timing_of_disposals,
    strategy_directors_loan_s455,
    strategy_gift_aid_relief,
    strategy_salary_sacrifice,
)

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731


class TestGiftAid:
    def test_higher_rate_donor_gets_the_rate_difference(self):
        # 800 net -> 1,000 gross. Earned 60,000 -> taxable 47,430; basic band
        # 37,700 extends to 38,700, so 1,000 of income moves from 40% to 20%
        # = 200 personal relief. The charity separately reclaims 200.
        result = strategy_gift_aid_relief(
            {"earned_income": 60000, "gift_aid_donation": 800}, TAX_YEAR
        )
        assert result["gross_donation"] == approx(1000.0)
        assert result["charity_reclaims"] == approx(200.0)
        assert result["personal_higher_rate_relief"] == approx(200.0)
        assert result["total_tax_benefit"] == approx(400.0)

    def test_donation_restores_personal_allowance_in_the_taper(self):
        # Earned 110,000: adjusted net income 110,000, PA tapered to 7,570.
        # 8,000 net -> 10,000 gross reduces ANI to 100,000, restoring the full
        # 12,570 PA, and extends the basic band by 10,000. Tax falls from
        # 33,432 to 29,432 = 4,000 personal relief (40% effective on the
        # 10,000 gift), and 5,000 of PA is restored.
        result = strategy_gift_aid_relief(
            {"earned_income": 110000, "gift_aid_donation": 8000}, TAX_YEAR
        )
        assert result["gross_donation"] == approx(10000.0)
        assert result["personal_higher_rate_relief"] == approx(4000.0)
        assert result["personal_allowance_restored"] == approx(5000.0)

    def test_basic_rate_donor_gets_no_extra_personal_relief(self):
        # Earned 30,000 -> taxable 17,430, entirely within the basic band even
        # before extension, so extending the band changes nothing: the only
        # relief is the 20% the charity reclaims.
        result = strategy_gift_aid_relief(
            {"earned_income": 30000, "gift_aid_donation": 800}, TAX_YEAR
        )
        assert result["personal_higher_rate_relief"] == approx(0.0)
        assert result["personal_allowance_restored"] == approx(0.0)
        assert result["charity_reclaims"] == approx(200.0)


class TestDirectorsLoanS455:
    def test_partly_repaid_in_time(self):
        # 50,000 overdrawn, 20,000 repaid within 9 months -> 30,000 still
        # outstanding at 33.75% = 10,125. Repaying in time avoided 6,750
        # (the difference from the 16,875 charge on the full 50,000).
        result = strategy_directors_loan_s455(
            {"overdrawn_loan_balance": 50000, "repaid_within_9_months": 20000}, TAX_YEAR
        )
        assert result["outstanding_after_deadline"] == approx(30000.0)
        assert result["s455_charge"] == approx(10125.0)
        assert result["charge_avoided_by_repaying_in_time"] == approx(6750.0)
        assert result["beneficial_loan_reportable"] is True

    def test_fully_repaid_in_time_avoids_the_charge(self):
        # 40,000 overdrawn, all repaid within the window -> no charge; the
        # full 40,000 x 33.75% = 13,500 was avoided.
        result = strategy_directors_loan_s455(
            {"overdrawn_loan_balance": 40000, "repaid_within_9_months": 40000}, TAX_YEAR
        )
        assert result["s455_charge"] == approx(0.0)
        assert result["charge_avoided_by_repaying_in_time"] == approx(13500.0)

    def test_nothing_repaid(self):
        # 25,000 outstanding at 33.75% = 8,437.50.
        result = strategy_directors_loan_s455(
            {"overdrawn_loan_balance": 25000}, TAX_YEAR
        )
        assert result["s455_charge"] == approx(8437.50)


class TestTimingOfDisposals:
    def test_splitting_uses_a_second_exemption_and_band(self):
        # Share gain 15,000, earned 42,270. Whole year: 12,000 taxable, 8,000
        # @ 18% + 4,000 @ 24% = 2,400. Split 7,500 each: 4,500 taxable, both
        # within the basic band @ 18% = 810 each = 1,620. Saving 780.
        result = strategy_cgt_timing_of_disposals(
            {"disposal_gain": 15000, "asset_type": "other", "earned_income": 42270}, TAX_YEAR
        )
        assert result["cgt_if_sold_in_one_year"] == approx(2400.0)
        assert result["cgt_if_split_over_two_years"] == approx(1620.0)
        assert result["saving_from_splitting"] == approx(780.0)

    def test_small_gain_split_falls_entirely_within_two_exemptions(self):
        # Gain 5,000: whole year 2,000 taxable @ 18% = 360. Split 2,500 each,
        # both under the 3,000 exemption, so nil CGT — the whole 360 saved.
        result = strategy_cgt_timing_of_disposals(
            {"disposal_gain": 5000, "asset_type": "other", "earned_income": 30000}, TAX_YEAR
        )
        assert result["cgt_if_sold_in_one_year"] == approx(360.0)
        assert result["cgt_if_split_over_two_years"] == approx(0.0)
        assert result["saving_from_splitting"] == approx(360.0)


class TestCapitalAllowances:
    def test_spend_within_aia_is_fully_relieved(self):
        # 50,000 is within the 1,000,000 AIA -> 50,000 first-year allowance;
        # at 25% CT that saves 12,500.
        result = strategy_capital_allowances(
            {"qualifying_spend": 50000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["annual_investment_allowance_used"] == approx(50000.0)
        assert result["first_year_allowance"] == approx(50000.0)
        assert result["tax_saved_year_one"] == approx(12500.0)

    def test_spend_above_aia_writes_down_the_excess(self):
        # 1,200,000: 1,000,000 AIA + 200,000 at the 18% WDA (36,000) =
        # 1,036,000 first-year allowance; at 25% that saves 259,000.
        result = strategy_capital_allowances(
            {"qualifying_spend": 1200000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["annual_investment_allowance_used"] == approx(1000000.0)
        assert result["written_down_first_year"] == approx(36000.0)
        assert result["first_year_allowance"] == approx(1036000.0)
        assert result["tax_saved_year_one"] == approx(259000.0)

    def test_marginal_rate_defaults_to_ct_main_rate(self):
        # No marginal_rate given -> uses the 25% CT main rate from the seed.
        result = strategy_capital_allowances({"qualifying_spend": 50000}, TAX_YEAR)
        assert result["marginal_rate"] == approx(0.25)
        assert result["tax_saved_year_one"] == approx(12500.0)


class TestSalarySacrifice:
    def test_basic_rate_saver_keeps_it_and_ni(self):
        # Salary 50,000, sacrifice 5,000 (both years in the 20%/8% bands).
        # IT: 50,000 -> 7,486; 45,000 -> 6,486 = 1,000 saved (20% of 5,000).
        # EE NIC: 37,430*8% = 2,994.40; 32,430*8% = 2,594.40 = 400 (8%).
        # Employee saves 1,400. ER NIC: 45,000*15% = 6,750 vs 40,000*15% =
        # 6,000 = 750. 5,000 goes into the pension; net cost 3,600.
        result = strategy_salary_sacrifice(
            {"salary": 50000, "sacrifice_amount": 5000}, TAX_YEAR
        )
        assert result["salary_sacrificed"] == approx(5000.0)
        assert result["employee_income_tax_and_ni_saved"] == approx(1400.0)
        assert result["employer_ni_saved"] == approx(750.0)
        assert result["into_pension"] == approx(5000.0)
        assert result["net_cost_of_pension_to_employee"] == approx(3600.0)
        assert result["total_saving"] == approx(2150.0)

    def test_higher_rate_saver_sacrifices_above_the_uel(self):
        # Salary 70,000, sacrifice 10,000 -> reduced 60,000, all sacrificed
        # income is above the UEL. IT: 70,000 -> 15,432; 60,000 -> 11,432 =
        # 4,000 (40% of 10,000). EE NIC on income above the 50,270 UEL is 2%,
        # so 10,000*2% = 200. Employee saves 4,200. ER NIC 15% of 10,000 =
        # 1,500. Net cost 10,000 - 4,200 = 5,800.
        result = strategy_salary_sacrifice(
            {"salary": 70000, "sacrifice_amount": 10000}, TAX_YEAR
        )
        assert result["employee_income_tax_and_ni_saved"] == approx(4200.0)
        assert result["employer_ni_saved"] == approx(1500.0)
        assert result["into_pension"] == approx(10000.0)
        assert result["net_cost_of_pension_to_employee"] == approx(5800.0)
        assert result["total_saving"] == approx(5700.0)

    def test_sacrifice_is_capped_at_salary_and_never_negative(self):
        # Sacrifice cannot exceed the salary. 3,000 salary is below every
        # threshold, so there is no tax/NIC to save, but the full 3,000 still
        # goes into the pension.
        result = strategy_salary_sacrifice(
            {"salary": 3000, "sacrifice_amount": 5000}, TAX_YEAR
        )
        assert result["salary_sacrificed"] == approx(3000.0)
        assert result["employee_income_tax_and_ni_saved"] == approx(0.0)
        assert result["employer_ni_saved"] == approx(0.0)
        assert result["into_pension"] == approx(3000.0)
