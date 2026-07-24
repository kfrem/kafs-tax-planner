"""Tier-1 planning strategies (see docs/TAX_PLANNING_COVERAGE.md). All
expected values hand-computed from published 2025/26 rates, with the working
shown in the comment."""

import pytest

from ruleengine.calculators import (
    strategy_business_property_relief,
    strategy_capital_allowances,
    strategy_cgt_rollover_relief,
    strategy_cgt_timing_of_disposals,
    strategy_charity_gift_of_assets,
    strategy_commercial_property_fixtures,
    strategy_directors_loan_s455,
    strategy_employer_pension_contribution,
    strategy_eot_disposal_relief,
    strategy_gift_aid_relief,
    strategy_group_loss_relief,
    strategy_income_timing,
    strategy_isa_bed_and_isa,
    strategy_life_policy_in_trust,
    strategy_partnership_profit_allocation,
    strategy_patent_box,
    strategy_payroll_giving,
    strategy_pension_death_benefit,
    strategy_personal_pension_contribution,
    strategy_property_income_finance_cost,
    strategy_property_incorporation,
    strategy_rd_tax_relief,
    strategy_relevant_property_trust_charges,
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


class TestPartnershipProfitAllocation:
    def test_shifting_share_to_the_lower_rate_partner_saves_tax(self):
        # 100k profit; partner A also has 40k other income (so their share is
        # taxed at 40%), partner B has none. 50/50: A pays IT(90k)=23,432 +
        # Class4(50k)=2,245.80; B pays IT(50k)=7,486 + 2,245.80 => 35,409.60.
        # 30/70: A IT(70k)=15,432 + Class4(30k)=1,045.80; B IT(70k)=15,432 +
        # Class4(70k)=2,656.60 => 34,566.40. Saving 843.20.
        result = strategy_partnership_profit_allocation(
            {"total_profit": 100000, "partner1_other_income": 40000,
             "partner2_other_income": 0, "current_partner1_share": 0.5,
             "proposed_partner1_share": 0.3}, TAX_YEAR
        )
        assert result["current_total_tax"] == approx(35409.60)
        assert result["proposed_total_tax"] == approx(34566.40)
        assert result["tax_saving"] == approx(843.20)
        assert result["current"]["partner1_tax"] == approx(25677.80)
        assert result["proposed"]["partner2_tax"] == approx(18088.60)

    def test_equalising_identical_partners_saves_tax(self):
        # Two partners with identical 10k other income. An unequal 40/60 split
        # pushes partner B into the 40% band while partner A wastes basic-rate
        # room. Current 40/60: 7,051.80 + 12,757.80 = 19,809.60. Proposed 50/50:
        # 9,131.80 each = 18,263.60. Equalising saves 1,546.00.
        result = strategy_partnership_profit_allocation(
            {"total_profit": 80000, "partner1_other_income": 10000,
             "partner2_other_income": 10000, "current_partner1_share": 0.4,
             "proposed_partner1_share": 0.5}, TAX_YEAR
        )
        assert result["current_total_tax"] == approx(19809.60)
        assert result["proposed_total_tax"] == approx(18263.60)
        assert result["tax_saving"] == approx(1546.00)

    def test_n_partner_firm_taxes_each_share(self):
        # 90k profit split 40/35/25 (36k/31.5k/22.5k); partners' other income
        # 50k/10k/0 -> tax 23,237.80 + 6,921.80 + 2,581.80 = 32,741.40.
        result = strategy_partnership_profit_allocation(
            {"total_profit": 90000, "partners": [
                {"profit_share": 0.4, "other_income": 50000},
                {"profit_share": 0.35, "other_income": 10000},
                {"profit_share": 0.25, "other_income": 0},
            ]}, TAX_YEAR
        )
        assert result["number_of_partners"] == 3
        assert result["total_tax"] == approx(32741.40)
        assert result["partners"][0]["tax"] == approx(23237.80)


class TestRelevantPropertyTrust:
    def test_all_three_charges_hand_computed(self):
        # 500k settled, 325k NRB -> 20% entry on the 175k excess = 35,000.
        # 600k at the ten-year point -> 6% of the 275k excess = 16,500 (an
        # effective 2.75% of the whole fund). A 100k exit 20 quarters (5 years)
        # into the next cycle -> 2.75% x 20/40 x 100k = 1,375.
        result = strategy_relevant_property_trust_charges(
            {"amount_settled": 500000, "trust_value": 600000,
             "amount_distributed": 100000, "quarters_since_last_charge": 20}, TAX_YEAR
        )
        assert result["entry_charge"] == approx(35000.0)
        assert result["ten_year_charge"] == approx(16500.0)
        assert result["ten_year_effective_rate"] == approx(0.0275)
        assert result["exit_charge"] == approx(1375.0)

    def test_fund_within_the_nil_rate_band_bears_no_charge(self):
        # A 300k fund is below the 325k band, so there is no entry or ten-year
        # charge (the classic "nil-rate band discretionary trust").
        result = strategy_relevant_property_trust_charges(
            {"amount_settled": 300000, "trust_value": 300000}, TAX_YEAR
        )
        assert result["entry_charge"] == approx(0.0)
        assert result["ten_year_charge"] == approx(0.0)

    def test_reduced_available_nrb_from_prior_transfers(self):
        # Prior chargeable transfers cut the available band to 125,000, so the
        # 20% entry charge bites on 500k - 125k = 375k = 75,000.
        result = strategy_relevant_property_trust_charges(
            {"amount_settled": 500000, "trust_value": 500000, "available_nrb": 125000},
            TAX_YEAR
        )
        assert result["entry_charge"] == approx(75000.0)

    def test_same_day_related_settlements_share_the_nil_rate_band(self):
        # 200,000 of same-day related settlements cut the 325,000 band to
        # 125,000, so the entry charge bites on 375,000 = 75,000 (the
        # anti-Rysaffe multiple-trust rule).
        result = strategy_relevant_property_trust_charges(
            {"amount_settled": 500000, "trust_value": 500000,
             "same_day_settlements_value": 200000}, TAX_YEAR
        )
        assert result["available_nrb"] == approx(125000.0)
        assert result["entry_charge"] == approx(75000.0)


class TestPropertyIncorporation:
    def test_break_even_with_s162_relief(self):
        # Higher-rate landlord: 50k rental profit + 40k other income. Personal
        # s.24 tax on the rental = IT(90k)-IT(40k) (17,946) less a 6,000 reducer
        # = 11,946. Company CT on 20k (after 30k interest) = 3,800; annual
        # saving 8,146. SDLT on a £1m transfer at additional rates = 93,750;
        # s.162 defers the CGT, so break-even = 93,750 / 8,146 = 11.51 years.
        result = strategy_property_incorporation(
            {"portfolio_value": 1000000, "rental_profit": 50000, "finance_costs": 30000,
             "other_income": 40000, "latent_gain": 300000, "s162_relief_available": True},
            TAX_YEAR
        )
        assert result["personal_annual_tax"] == approx(11946.0)
        assert result["company_annual_tax"] == approx(3800.0)
        assert result["annual_tax_saving"] == approx(8146.0)
        assert result["sdlt_on_transfer"] == approx(93750.0)
        assert result["cgt_on_transfer"] == approx(0.0)
        assert result["break_even_years"] == approx(11.51)

    def test_without_s162_the_cgt_lengthens_the_payback(self):
        # No s.162 relief: the 300k latent gain is taxed now at the 24%
        # residential rate = 72,000, so the one-off cost is 93,750 + 72,000 =
        # 165,750 and the break-even stretches to 20.35 years.
        result = strategy_property_incorporation(
            {"portfolio_value": 1000000, "rental_profit": 50000, "finance_costs": 30000,
             "other_income": 40000, "latent_gain": 300000, "s162_relief_available": False},
            TAX_YEAR
        )
        assert result["cgt_on_transfer"] == approx(72000.0)
        assert result["one_off_cost"] == approx(165750.0)
        assert result["break_even_years"] == approx(20.35)

    def test_basic_rate_landlord_gets_no_benefit(self):
        # A basic-rate landlord suffers no real s.24 penalty, so the company's
        # 19% CT actually costs more than staying personal — no saving, and the
        # break-even is undefined (incorporation would not pay).
        result = strategy_property_incorporation(
            {"portfolio_value": 300000, "rental_profit": 20000, "finance_costs": 15000,
             "other_income": 10000, "s162_relief_available": True},
            TAX_YEAR
        )
        assert result["annual_tax_saving"] < 0
        assert result["break_even_years"] is None

    def test_extraction_reduces_the_saving(self):
        # Drawing the 16,200 post-CT profit out as dividends (over 40k income,
        # taxable 27,430) costs 2,856.25 dividend tax, so the after-extraction
        # saving falls from 8,146 (retained) to 5,289.75.
        result = strategy_property_incorporation(
            {"portfolio_value": 1000000, "rental_profit": 50000, "finance_costs": 30000,
             "other_income": 40000, "latent_gain": 300000, "s162_relief_available": True,
             "extract_profits": True}, TAX_YEAR
        )
        assert result["annual_tax_saving"] == approx(8146.0)          # retained
        assert result["dividend_tax_on_extraction"] == approx(2856.25)
        assert result["company_total_tax_if_extracted"] == approx(6656.25)
        assert result["annual_saving_after_extraction"] == approx(5289.75)

    def test_transfer_land_tax_follows_the_jurisdiction(self):
        # Scotland uses LBTT (with the 8% ADS), not SDLT — a materially higher
        # transfer cost that must flow into the one-off cost.
        from ruleengine.calculators import lbtt_residential

        eng = strategy_property_incorporation(
            {"portfolio_value": 1000000, "rental_profit": 50000, "finance_costs": 30000,
             "other_income": 40000, "s162_relief_available": True}, TAX_YEAR
        )
        sco = strategy_property_incorporation(
            {"portfolio_value": 1000000, "rental_profit": 50000, "finance_costs": 30000,
             "other_income": 40000, "s162_relief_available": True, "jurisdiction": "scotland"},
            TAX_YEAR
        )
        expected_lbtt = lbtt_residential(
            {"price": 1000000, "additional_dwelling": True}, TAX_YEAR
        )["total_lbtt"]
        assert eng["land_tax_on_transfer"] == approx(93750.0)          # SDLT
        assert sco["land_tax_on_transfer"] == approx(expected_lbtt)    # LBTT
        assert sco["one_off_cost"] == approx(expected_lbtt)


class TestRdTaxRelief:
    def test_merged_scheme_net_benefit(self):
        # 100k qualifying spend -> 20% RDEC = 20k gross; taxable at 25% (5k);
        # net benefit 15k (about 15% of the spend for a main-rate company).
        result = strategy_rd_tax_relief(
            {"qualifying_rd_spend": 100000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["gross_credit"] == approx(20000.0)
        assert result["tax_on_credit"] == approx(5000.0)
        assert result["net_benefit"] == approx(15000.0)

    def test_marginal_rate_defaults_to_ct_main_rate(self):
        result = strategy_rd_tax_relief({"qualifying_rd_spend": 100000}, TAX_YEAR)
        assert result["net_benefit"] == approx(15000.0)  # 25% default


class TestPatentBox:
    def test_saving_vs_main_rate(self):
        # 200k patented-product profit at 10% (20k) vs the 25% main rate (50k)
        # = 30k saved.
        result = strategy_patent_box({"patent_profit": 200000, "marginal_rate": 0.25}, TAX_YEAR)
        assert result["tax_at_main_rate"] == approx(50000.0)
        assert result["tax_under_patent_box"] == approx(20000.0)
        assert result["tax_saving"] == approx(30000.0)


class TestCommercialPropertyFixtures:
    def test_fixtures_within_the_aia(self):
        # 200k fixtures fully within the 1m AIA -> 200k first-year allowance;
        # at 25% that saves 50k.
        result = strategy_commercial_property_fixtures(
            {"fixtures_value": 200000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["aia_used"] == approx(200000.0)
        assert result["first_year_allowance"] == approx(200000.0)
        assert result["tax_saved_year_one"] == approx(50000.0)

    def test_excess_over_aia_uses_special_rate_wda(self):
        # 1.2m fixtures: 1m AIA + 200k at the 6% special rate (12k) = 1,012,000
        # first-year allowance; at 25% that saves 253,000.
        result = strategy_commercial_property_fixtures(
            {"fixtures_value": 1200000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["aia_used"] == approx(1000000.0)
        assert result["written_down_first_year"] == approx(12000.0)
        assert result["first_year_allowance"] == approx(1012000.0)
        assert result["tax_saved_year_one"] == approx(253000.0)


class TestEotDisposalRelief:
    def test_eot_sale_saves_the_whole_cgt(self):
        # 2m gain: a normal sale bears BADR 14% on the first 1m (140k) + 24% on
        # the next 1m (240k) = 380k; the EOT sale is exempt, so 380k is saved.
        result = strategy_eot_disposal_relief(
            {"disposal_gain": 2000000, "badr_available": True, "badr_lifetime_used": 0}, TAX_YEAR
        )
        assert result["cgt_without_eot"] == approx(380000.0)
        assert result["cgt_under_eot"] == approx(0.0)
        assert result["cgt_saved"] == approx(380000.0)

    def test_without_badr_the_whole_gain_is_at_the_standard_rate(self):
        # No BADR: 500k gain all at the 24% share rate = 120k, all saved by EOT.
        result = strategy_eot_disposal_relief(
            {"disposal_gain": 500000, "badr_available": False}, TAX_YEAR
        )
        assert result["cgt_saved"] == approx(120000.0)


class TestPensionDeathBenefit:
    def test_pot_brought_into_estate_from_2027(self):
        # 500k pot, estate above the NRB -> 40% = 200k extra IHT from April 2027
        # (zero before).
        result = strategy_pension_death_benefit(
            {"pension_pot_value": 500000, "estate_above_nrb": True}, TAX_YEAR
        )
        assert result["iht_before_april_2027"] == approx(0.0)
        assert result["iht_from_april_2027"] == approx(200000.0)
        assert result["extra_iht_from_reform"] == approx(200000.0)

    def test_estate_within_nrb_bears_no_charge(self):
        result = strategy_pension_death_benefit(
            {"pension_pot_value": 500000, "estate_above_nrb": False}, TAX_YEAR
        )
        assert result["extra_iht_from_reform"] == approx(0.0)


class TestLifePolicyInTrust:
    def test_in_trust_saves_iht_on_the_payout(self):
        # 400k sum assured, estate above the NRB: held personally it would add
        # 40% = 160k IHT; in trust it is outside the estate (0), so 160k saved
        # and the full 400k is available to pay the bill.
        result = strategy_life_policy_in_trust(
            {"sum_assured": 400000, "estate_above_nrb": True}, TAX_YEAR
        )
        assert result["iht_if_held_personally"] == approx(160000.0)
        assert result["iht_if_written_in_trust"] == approx(0.0)
        assert result["iht_saved_by_writing_in_trust"] == approx(160000.0)
        assert result["payout_available_for_iht_bill"] == approx(400000.0)
