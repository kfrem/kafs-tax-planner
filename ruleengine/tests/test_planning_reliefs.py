"""Tier-1 planning strategies (see docs/TAX_PLANNING_COVERAGE.md). All
expected values hand-computed from published 2025/26 rates, with the working
shown in the comment."""

import pytest

from ruleengine.calculators import (
    strategy_business_property_relief,
    strategy_capital_allowances,
    strategy_cgt_timing_of_disposals,
    strategy_directors_loan_s455,
    strategy_employer_pension_contribution,
    strategy_gift_aid_relief,
    strategy_group_loss_relief,
    strategy_isa_bed_and_isa,
    strategy_personal_pension_contribution,
    strategy_property_income_finance_cost,
    strategy_salary_sacrifice,
    strategy_venture_capital_investment,
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


class TestPersonalPensionContribution:
    def test_sixty_percent_relief_inside_the_taper(self):
        # Earned 110,000, 10,000 gross contribution. Without: PA tapered to
        # 7,570, tax 33,432. With: 10,000 reduces ANI to 100,000 (PA fully
        # restored to 12,570) and extends the basic band by 10,000, tax 29,432
        # = 4,000 saved. Plus the 2,000 basic-rate credit HMRC adds = 6,000
        # relief on a 10,000 contribution = 60% effective; net cost 4,000.
        result = strategy_personal_pension_contribution(
            {"earned_income": 110000, "desired_contribution": 10000}, TAX_YEAR
        )
        assert result["relievable_gross"] == approx(10000.0)
        assert result["basic_rate_credit_to_pension"] == approx(2000.0)
        assert result["higher_rate_and_taper_saving"] == approx(4000.0)
        assert result["personal_allowance_restored"] == approx(5000.0)
        assert result["total_relief_value"] == approx(6000.0)
        assert result["effective_relief_rate"] == approx(0.60)
        assert result["net_cost_to_member"] == approx(4000.0)

    def test_basic_rate_taxpayer_gets_only_the_source_relief(self):
        # Earned 40,000: taxable 27,430 is already inside the basic band, so
        # extending the band changes no tax. Relief is just the 20% credit
        # (1,000 on 5,000) = 20% effective; net cost 4,000.
        result = strategy_personal_pension_contribution(
            {"earned_income": 40000, "desired_contribution": 5000}, TAX_YEAR
        )
        assert result["basic_rate_credit_to_pension"] == approx(1000.0)
        assert result["higher_rate_and_taper_saving"] == approx(0.0)
        assert result["personal_allowance_restored"] == approx(0.0)
        assert result["total_relief_value"] == approx(1000.0)
        assert result["effective_relief_rate"] == approx(0.20)
        assert result["net_cost_to_member"] == approx(4000.0)

    def test_relief_capped_at_relevant_earnings_not_dividends(self):
        # 5,000 earnings but a 10,000 desired contribution: relief is capped at
        # max(3,600, 5,000) = 5,000; the other 5,000 is unrelieved. Dividends
        # do not lift the cap (FA 2004 s.190).
        result = strategy_personal_pension_contribution(
            {
                "earned_income": 5000,
                "dividend_income": 50000,
                "desired_contribution": 10000,
                "relevant_uk_earnings": 5000,
            },
            TAX_YEAR,
        )
        assert result["relievable_gross"] == approx(5000.0)
        assert result["unrelieved_amount"] == approx(5000.0)


class TestEmployerPensionContribution:
    def test_ct_saving_and_ni_avoided_at_the_main_rate(self):
        # 300,000 profit is above the 250,000 upper limit -> flat 25%. A 20,000
        # contribution cuts CT from 75,000 to 70,000 = 5,000. Paying the same
        # as salary would have cost 20,000*15% = 3,000 employer NIC, which the
        # pension route avoids. Net cost after CT relief 15,000.
        result = strategy_employer_pension_contribution(
            {"company_profit": 300000, "contribution": 20000}, TAX_YEAR
        )
        assert result["contribution"] == approx(20000.0)
        assert result["corporation_tax_saving"] == approx(5000.0)
        assert result["employer_ni_saved_vs_salary"] == approx(3000.0)
        assert result["no_relevant_earnings_cap"] is True
        assert result["net_cost_to_company"] == approx(15000.0)

    def test_contribution_capped_at_available_profit(self):
        # A 60,000 contribution against 50,000 profit is capped at 50,000
        # (the deduction cannot exceed the profit). 50,000 profit is at the
        # small-profits limit -> 19%, so CT falls 9,500 to nil = 9,500.
        result = strategy_employer_pension_contribution(
            {"company_profit": 50000, "contribution": 60000}, TAX_YEAR
        )
        assert result["contribution"] == approx(50000.0)
        assert result["corporation_tax_saving"] == approx(9500.0)


class TestGroupLossRelief:
    def test_surrender_into_the_marginal_band_relieves_at_26_5_percent(self):
        # 50,000 loss into a 250,000-profit claimant. CT on 250,000 is 62,500
        # (25% flat at the upper limit); CT on 200,000 is 50,000 - 750 marginal
        # relief = 49,250. Saved 13,250 = 26.5% on the 50,000 relieved — the
        # marginal rate, better than a 19%/25% carry-forward.
        result = strategy_group_loss_relief(
            {"claimant_company_profit": 250000, "surrendering_company_loss": 50000},
            TAX_YEAR,
        )
        assert result["loss_surrendered"] == approx(50000.0)
        assert result["corporation_tax_saved"] == approx(13250.0)
        assert result["effective_relief_rate"] == approx(0.265)
        assert result["unrelieved_loss_carried_forward"] == approx(0.0)

    def test_surrender_above_the_upper_limit_relieves_at_the_main_rate(self):
        # 100,000 loss into a 500,000-profit claimant (well above the 250,000
        # upper limit -> flat 25%). CT 125,000 -> 100,000 = 25,000 saved = 25%.
        result = strategy_group_loss_relief(
            {"claimant_company_profit": 500000, "surrendering_company_loss": 100000},
            TAX_YEAR,
        )
        assert result["corporation_tax_saved"] == approx(25000.0)
        assert result["effective_relief_rate"] == approx(0.25)

    def test_loss_exceeding_claimant_profit_carries_the_balance_forward(self):
        # 300,000 loss but only 200,000 profit: 200,000 is relieved now (claimant
        # profit to nil) and 100,000 is carried forward in the loss company.
        result = strategy_group_loss_relief(
            {"claimant_company_profit": 200000, "surrendering_company_loss": 300000},
            TAX_YEAR,
        )
        assert result["loss_surrendered"] == approx(200000.0)
        assert result["claimant_profit_after"] == approx(0.0)
        assert result["unrelieved_loss_carried_forward"] == approx(100000.0)


class TestIsaBedAndIsa:
    def test_within_the_exemption_no_cgt_and_dividends_sheltered(self):
        # Higher-rate investor shelters 20,000 (the full ISA limit). A 2,500
        # gain is inside the 3,000 annual exemption -> no CGT on transfer. 800
        # of annual dividends then escape the 33.75% upper rate = 270 a year.
        result = strategy_isa_bed_and_isa(
            {
                "amount_to_shelter": 20000,
                "realised_gain": 2500,
                "annual_dividend_income": 800,
                "is_higher_rate": True,
            },
            TAX_YEAR,
        )
        assert result["amount_sheltered"] == approx(20000.0)
        assert result["isa_allowance_remaining"] == approx(0.0)
        assert result["gain_covered_by_exemption"] == approx(2500.0)
        assert result["cgt_payable_on_transfer"] == approx(0.0)
        assert result["annual_dividend_tax_saved"] == approx(270.0)

    def test_gain_above_the_exemption_crystallises_cgt(self):
        # 5,000 gain, none of the exemption used elsewhere: 2,000 is taxable at
        # the 24% higher rate for shares = 480 CGT on the transfer.
        result = strategy_isa_bed_and_isa(
            {"amount_to_shelter": 20000, "realised_gain": 5000, "is_higher_rate": True},
            TAX_YEAR,
        )
        assert result["gain_covered_by_exemption"] == approx(3000.0)
        assert result["cgt_payable_on_transfer"] == approx(480.0)

    def test_amount_capped_at_the_isa_limit(self):
        # A 30,000 intention is capped at the 20,000 annual subscription limit.
        result = strategy_isa_bed_and_isa(
            {"amount_to_shelter": 30000}, TAX_YEAR
        )
        assert result["amount_sheltered"] == approx(20000.0)
        assert result["isa_allowance_remaining"] == approx(0.0)

    def test_basic_rate_investor_uses_the_ordinary_dividend_rate(self):
        # A basic-rate investor's sheltered dividends escape only the 8.75%
        # ordinary rate: 1,000 * 8.75% = 87.50.
        result = strategy_isa_bed_and_isa(
            {
                "amount_to_shelter": 10000,
                "annual_dividend_income": 1000,
                "is_higher_rate": False,
            },
            TAX_YEAR,
        )
        assert result["annual_dividend_tax_saved"] == approx(87.50)


class TestBusinessPropertyRelief:
    def test_pre_reform_unlimited_100pc_relief(self):
        # 2025/26: a 2,000,000 qualifying business is wholly relieved (no cap),
        # leaving nothing taxable and saving 800,000 of IHT at 40%.
        result = strategy_business_property_relief(
            {"qualifying_value": 2000000}, TAX_YEAR
        )
        assert result["full_relief_cap"] is None
        assert result["total_relieved_value"] == approx(2000000.0)
        assert result["taxable_value_after_relief"] == approx(0.0)
        assert result["iht_saved_by_relief"] == approx(800000.0)

    def test_reformed_1m_cap_from_2026_27(self):
        # 2026/27: the same 2,000,000 gets 100% on the first 1,000,000 and 50%
        # on the rest = 1,500,000 relieved, 500,000 taxable, 600,000 IHT saved
        # — 200,000 more IHT than before the cap.
        result = strategy_business_property_relief(
            {"qualifying_value": 2000000}, "2026/27"
        )
        assert result["full_relief_cap"] == 1000000
        assert result["value_relieved_at_100pc"] == approx(1000000.0)
        assert result["value_above_cap"] == approx(1000000.0)
        assert result["total_relieved_value"] == approx(1500000.0)
        assert result["taxable_value_after_relief"] == approx(500000.0)
        assert result["iht_saved_by_relief"] == approx(600000.0)

    def test_business_within_the_cap_is_unaffected_by_the_reform(self):
        # An 800,000 business is below the 1,000,000 cap, so it is still wholly
        # relieved in 2026/27 — the reform only bites above 1,000,000.
        result = strategy_business_property_relief(
            {"qualifying_value": 800000}, "2026/27"
        )
        assert result["total_relieved_value"] == approx(800000.0)
        assert result["taxable_value_after_relief"] == approx(0.0)
        assert result["iht_saved_by_relief"] == approx(320000.0)


class TestVentureCapitalInvestment:
    def test_eis_30pc_relief_and_gain_deferral(self):
        # EIS: 100,000 -> 30% = 30,000 relief (within the 50,000 IT bill). A
        # 40,000 gain reinvested is deferred at the 24% share rate = 9,600.
        # Net cost 100,000 - 30,000 = 70,000 (the deferred CGT is postponed,
        # not saved, so it does not reduce the net cost).
        result = strategy_venture_capital_investment(
            {
                "scheme": "eis",
                "amount_invested": 100000,
                "income_tax_liability": 50000,
                "gain_reinvested": 40000,
                "is_higher_rate": True,
            },
            TAX_YEAR,
        )
        assert result["income_tax_relief"] == approx(30000.0)
        assert result["cgt_deferred"] == approx(9600.0)
        assert result["cgt_permanently_saved"] == approx(0.0)
        assert result["net_cost_after_relief"] == approx(70000.0)

    def test_seis_50pc_relief_and_reinvestment_exemption(self):
        # SEIS: 100,000 -> 50% = 50,000 relief. Half of the 40,000 reinvested
        # gain (20,000) is permanently exempt = 20,000 * 24% = 4,800 CGT saved.
        # Net cost 100,000 - 50,000 - 4,800 = 45,200.
        result = strategy_venture_capital_investment(
            {
                "scheme": "seis",
                "amount_invested": 100000,
                "income_tax_liability": 60000,
                "gain_reinvested": 40000,
                "is_higher_rate": True,
            },
            TAX_YEAR,
        )
        assert result["income_tax_relief"] == approx(50000.0)
        assert result["cgt_permanently_saved"] == approx(4800.0)
        assert result["cgt_deferred"] == approx(0.0)
        assert result["net_cost_after_relief"] == approx(45200.0)

    def test_vct_relief_capped_at_the_income_tax_bill(self):
        # VCT: 50,000 would give 15,000 relief, but the IT bill is only 10,000
        # so relief is capped there. Dividends are tax-free; no CGT deferral.
        result = strategy_venture_capital_investment(
            {
                "scheme": "vct",
                "amount_invested": 50000,
                "income_tax_liability": 10000,
                "is_higher_rate": True,
            },
            TAX_YEAR,
        )
        assert result["income_tax_relief"] == approx(10000.0)
        assert result["capped_by_income_tax_liability"] is True
        assert result["tax_free_dividends"] is True
        assert result["cgt_deferred"] == approx(0.0)
        assert result["net_cost_after_relief"] == approx(40000.0)

    def test_investment_above_the_annual_limit_is_capped(self):
        # EIS annual limit is 1,000,000: a 1,200,000 investment is relieved on
        # 1,000,000 -> 300,000 relief (ample IT bill).
        result = strategy_venture_capital_investment(
            {
                "scheme": "eis",
                "amount_invested": 1200000,
                "income_tax_liability": 500000,
                "is_higher_rate": True,
            },
            TAX_YEAR,
        )
        assert result["eligible_investment"] == approx(1000000.0)
        assert result["income_tax_relief"] == approx(300000.0)


class TestPropertyIncomeFinanceCost:
    def test_higher_rate_landlord_pays_the_s24_penalty(self):
        # 24,000 rent - 4,000 expenses = 20,000 profit; 50,000 other income.
        # Tax on 70,000 = 15,432, less a 20% reducer on 10,000 interest (2,000)
        # = 13,432. Full deduction (tax on 60,000) = 11,432. s.24 costs 2,000
        # extra — the interest relieved at 20% instead of the 40% it saves.
        result = strategy_property_income_finance_cost(
            {"rental_income": 24000, "allowable_expenses": 4000,
             "finance_costs": 10000, "other_income": 50000}, TAX_YEAR
        )
        assert result["rental_profit"] == approx(20000.0)
        assert result["basic_rate_tax_reducer"] == approx(2000.0)
        assert result["tax_under_s24"] == approx(13432.0)
        assert result["tax_if_interest_fully_deductible"] == approx(11432.0)
        assert result["extra_tax_from_restriction"] == approx(2000.0)

    def test_basic_rate_landlord_is_unaffected(self):
        # 15,000 rent - 3,000 = 12,000 profit; 20,000 other income keeps the
        # landlord in the basic band, where the 20% reducer exactly equals the
        # relief a full deduction would give — s.24 costs nothing.
        result = strategy_property_income_finance_cost(
            {"rental_income": 15000, "allowable_expenses": 3000,
             "finance_costs": 5000, "other_income": 20000}, TAX_YEAR
        )
        assert result["basic_rate_tax_reducer"] == approx(1000.0)
        assert result["extra_tax_from_restriction"] == approx(0.0)

    def test_reducer_capped_at_rental_profit(self):
        # Very geared: 18,000 rent - 3,000 = 15,000 profit but 20,000 interest.
        # The reducer is capped at the 15,000 profit (not the 20,000 interest),
        # and the unrelieved 5,000 of interest is carried forward.
        result = strategy_property_income_finance_cost(
            {"rental_income": 18000, "allowable_expenses": 3000,
             "finance_costs": 20000, "other_income": 50000}, TAX_YEAR
        )
        assert result["rental_profit"] == approx(15000.0)
        assert result["basic_rate_tax_reducer"] == approx(3000.0)  # 20% of 15,000
        assert result["finance_costs_carried_forward"] == approx(5000.0)
