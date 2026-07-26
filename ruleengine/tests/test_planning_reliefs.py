"""Tier-1 planning strategies (see docs/TAX_PLANNING_COVERAGE.md). All
expected values hand-computed from published 2025/26 rates, with the working
shown in the comment."""

import pytest

from ruleengine.calculators import (
    strategy_business_property_relief,
    strategy_capital_allowances,
    strategy_capital_allowances_full_expensing,
    strategy_cgt_rollover_relief,
    strategy_cgt_timing_of_disposals,
    strategy_charity_gift_of_assets,
    strategy_commercial_property_fixtures,
    strategy_directors_loan_s455,
    strategy_employer_pension_contribution,
    strategy_eot_disposal_relief,
    strategy_fhl_abolition_transition,
    strategy_gift_aid_relief,
    strategy_group_loss_relief,
    strategy_holding_company_structuring,
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
    strategy_sdlt_mixed_use_classification,
    strategy_sdlt_uninhabitable_classification,
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

    def test_reformed_2point5m_cap_from_2026_27(self):
        # 2026/27: the £1m cap originally announced was raised to £2.5m at
        # Autumn Budget 2025 (Finance Act 2026). A 3,500,000 business gets 100%
        # on the first 2,500,000 and 50% on the 1,000,000 excess = 3,000,000
        # relieved, 500,000 taxable, 1,200,000 IHT saved at 40% — the 500,000
        # excess bears 200,000 IHT it would not have before the cap.
        result = strategy_business_property_relief(
            {"qualifying_value": 3500000}, "2026/27"
        )
        assert result["full_relief_cap"] == 2500000
        assert result["value_relieved_at_100pc"] == approx(2500000.0)
        assert result["value_above_cap"] == approx(1000000.0)
        assert result["total_relieved_value"] == approx(3000000.0)
        assert result["taxable_value_after_relief"] == approx(500000.0)
        assert result["iht_saved_by_relief"] == approx(1200000.0)

    def test_business_within_the_cap_is_unaffected_by_the_reform(self):
        # A 2,000,000 business is below the 2,500,000 cap, so it is still wholly
        # relieved in 2026/27 — the reform only bites above 2,500,000.
        result = strategy_business_property_relief(
            {"qualifying_value": 2000000}, "2026/27"
        )
        assert result["full_relief_cap"] == 2500000
        assert result["total_relieved_value"] == approx(2000000.0)
        assert result["taxable_value_after_relief"] == approx(0.0)
        assert result["iht_saved_by_relief"] == approx(800000.0)


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
    def test_eot_sale_before_26_nov_2025_is_fully_exempt(self):
        # 2m gain disposed 1 Jun 2025 (before the change): a normal sale bears
        # BADR 14% on the first 1m (140k) + 24% on the next 1m (240k) = 380k;
        # the EOT sale is fully exempt, so the whole 380k is saved.
        result = strategy_eot_disposal_relief(
            {"disposal_gain": 2000000, "badr_available": True,
             "badr_lifetime_used": 0, "disposal_date": "2025-06-01"},
            TAX_YEAR,
        )
        assert result["exempt_fraction"] == 1.0
        assert result["cgt_without_eot"] == approx(380000.0)
        assert result["cgt_under_eot"] == approx(0.0)
        assert result["cgt_saved"] == approx(380000.0)

    def test_eot_sale_on_or_after_26_nov_2025_taxes_half(self):
        # Same 2m gain disposed 1 Jun 2026 (after the FA 2026 s.35 change): a
        # normal sale bears BADR 18% on 1m (180k) + 24% on 1m (240k) = 420k;
        # under the EOT only 50% (1m) is exempt, the other 1m is chargeable at
        # 24% = 240k, so 180k is saved (no longer the full amount).
        result = strategy_eot_disposal_relief(
            {"disposal_gain": 2000000, "badr_available": True,
             "badr_lifetime_used": 0, "disposal_date": "2026-06-01"},
            "2026/27",
        )
        assert result["exempt_fraction"] == 0.5
        assert result["chargeable_gain_under_eot"] == approx(1000000.0)
        assert result["cgt_without_eot"] == approx(420000.0)
        assert result["cgt_under_eot"] == approx(240000.0)
        assert result["cgt_saved"] == approx(180000.0)

    def test_without_badr_before_the_change_the_whole_gain_is_saved(self):
        # No BADR, disposed before 26 Nov 2025: 500k gain all at the 24% share
        # rate = 120k, all saved by the full EOT exemption.
        result = strategy_eot_disposal_relief(
            {"disposal_gain": 500000, "badr_available": False,
             "disposal_date": "2025-06-01"},
            TAX_YEAR,
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


class TestIncomeTiming:
    def test_dividend_cheaper_this_year_before_the_2026_rise(self):
        # Earned 60,000 both years -> taxable 47,430, so the whole dividend
        # sits in the upper band. This year (2025/26): 20,000 x 33.75% less
        # the 500 allowance at 33.75% = 6,750.00 - 168.75 = 6,581.25. Next
        # year (2026/27, +2pp): 20,000 x 35.75% - 500 x 35.75% = 7,150.00 -
        # 178.75 = 6,971.25. Paying it this year saves 390.00 (19,500 x 2pp).
        result = strategy_income_timing(
            {"shiftable_amount": 20000, "income_type": "dividend",
             "earned_income": 60000},
            TAX_YEAR,
        )
        assert result["incremental_tax_this_year"] == approx(6581.25)
        assert result["incremental_tax_next_year"] == approx(6971.25)
        assert result["recommendation"] == "take_this_year"
        assert result["saving"] == approx(390.0)

    def test_bonus_deferred_out_of_the_taper_zone(self):
        # Bonus 10,000, earned income type. This year on 100,000: the bonus
        # tapers the PA by 5,000 (half the excess over 100,000), so tax is
        # 10,000 x 40% + 5,000 of re-taxed income x 40% = 6,000 (the 60%
        # effective zone). Next year on an expected 80,000: 10,000 x 40% =
        # 4,000. Deferring saves 2,000.
        result = strategy_income_timing(
            {"shiftable_amount": 10000, "income_type": "earned",
             "earned_income": 100000, "next_year_earned_income": 80000},
            TAX_YEAR,
        )
        assert result["incremental_tax_this_year"] == approx(6000.0)
        assert result["incremental_tax_next_year"] == approx(4000.0)
        assert result["recommendation"] == "defer_to_next_year"
        assert result["saving"] == approx(2000.0)

    def test_basic_rate_both_years_is_indifferent(self):
        # Earned 20,000 both years; 5,000 more stays within the basic band
        # in either year at the unchanged 20% rate = 1,000 both ways.
        result = strategy_income_timing(
            {"shiftable_amount": 5000, "income_type": "earned",
             "earned_income": 20000},
            TAX_YEAR,
        )
        assert result["incremental_tax_this_year"] == approx(1000.0)
        assert result["incremental_tax_next_year"] == approx(1000.0)
        assert result["recommendation"] == "indifferent"
        assert result["saving"] == approx(0.0)


class TestPayrollGiving:
    def test_higher_rate_employee_full_marginal_relief(self):
        # Salary 60,000 -> taxable 47,430, tax 11,432.00. Donating 1,200
        # pre-tax leaves taxable 46,230, tax 10,952.00: 480.00 saved (40%),
        # net cost 720.00, and the charity receives the whole 1,200.
        result = strategy_payroll_giving(
            {"earned_income": 60000, "annual_donation": 1200}, TAX_YEAR
        )
        assert result["charity_receives"] == approx(1200.0)
        assert result["income_tax_saved"] == approx(480.0)
        assert result["net_cost_to_donor"] == approx(720.0)

    def test_donation_in_the_taper_zone_gets_60_percent_relief(self):
        # Salary 110,000: PA tapered to 7,570, tax 33,432.00. A 10,000
        # pre-tax donation reduces pay to 100,000: full 12,570 PA restored,
        # tax 27,432.00 — 6,000 saved (60% effective) and 5,000 of PA back.
        result = strategy_payroll_giving(
            {"earned_income": 110000, "annual_donation": 10000}, TAX_YEAR
        )
        assert result["income_tax_saved"] == approx(6000.0)
        assert result["personal_allowance_restored"] == approx(5000.0)
        assert result["net_cost_to_donor"] == approx(4000.0)

    def test_donation_capped_at_pay(self):
        # A donation cannot exceed the pay it is deducted from: 5,000
        # requested against 1,000 of pay is capped at 1,000; pay was below
        # the personal allowance so no tax was saved.
        result = strategy_payroll_giving(
            {"earned_income": 1000, "annual_donation": 5000}, TAX_YEAR
        )
        assert result["annual_donation"] == approx(1000.0)
        assert result["income_tax_saved"] == approx(0.0)


class TestCharityGiftOfAssets:
    def test_double_relief_for_a_higher_rate_donor(self):
        # Earned 80,000 (taxable 67,430, tax 19,432.00). s.431 deducts the
        # 20,000 market value -> taxable 47,430, tax 11,432.00 = 8,000 income
        # tax saved (all at 40%). s.257 no-gain/no-loss: a sale would have
        # charged 10,000 - 3,000 AEA = 7,000 at 24% = 1,680 CGT avoided.
        # Total 9,680; net cost 20,000 - 8,000 = 12,000.
        result = strategy_charity_gift_of_assets(
            {"gift_value": 20000, "held_gain": 10000, "earned_income": 80000},
            TAX_YEAR,
        )
        assert result["income_tax_saved"] == approx(8000.0)
        assert result["cgt_avoided"] == approx(1680.0)
        assert result["total_tax_benefit"] == approx(9680.0)
        assert result["net_cost_of_gift"] == approx(12000.0)

    def test_basic_rate_donor_gain_within_aea(self):
        # Earned 30,000 + dividends 5,000. Relief 10,000 at 20% = 2,000 (the
        # dividends are untouched: earned absorbs the whole deduction). The
        # held gain of 2,000 is within the 3,000 AEA, so a sale would have
        # been tax-free anyway: cgt_avoided 0.
        result = strategy_charity_gift_of_assets(
            {"gift_value": 10000, "held_gain": 2000, "earned_income": 30000,
             "dividend_income": 5000},
            TAX_YEAR,
        )
        assert result["income_tax_saved"] == approx(2000.0)
        assert result["cgt_avoided"] == approx(0.0)
        assert result["net_cost_of_gift"] == approx(8000.0)

    def test_gift_larger_than_earned_income_relieves_dividends(self):
        # Earned 10,000 (below the 12,570 PA -> no earned tax). Dividends
        # 30,000: PA remainder 2,570 shelters some, taxable dividends 27,430
        # at 8.75% less the 500 allowance at 8.75% = 2,400.13 - 43.75 =
        # 2,356.38. A 15,000 gift takes earned to 0 and dividends to 25,000:
        # taxable dividends 12,430 -> 1,087.63 - 43.75 = 1,043.88. Saved
        # 1,312.50 (= 15,000 x 8.75%, the dividend marginal rate).
        result = strategy_charity_gift_of_assets(
            {"gift_value": 15000, "held_gain": 0, "earned_income": 10000,
             "dividend_income": 30000},
            TAX_YEAR,
        )
        assert result["income_tax_saved"] == approx(1312.50)
        assert result["cgt_avoided"] == approx(0.0)


class TestRolloverRelief:
    def test_partial_reinvestment_leaves_the_shortfall_chargeable(self):
        # Proceeds 500,000, gain 200,000, replacement 450,000: 50,000 not
        # reinvested is chargeable now (s.153), 150,000 rolled over. Earned
        # 60,000 -> income fills the basic band, so the 'other' 24% higher
        # rate applies. Without relief (200,000 - 3,000) x 24% = 47,280;
        # with relief (50,000 - 3,000) x 24% = 11,280; 36,000 deferred.
        result = strategy_cgt_rollover_relief(
            {"disposal_proceeds": 500000, "disposal_gain": 200000,
             "replacement_cost": 450000, "earned_income": 60000},
            TAX_YEAR,
        )
        assert result["amount_not_reinvested"] == approx(50000.0)
        assert result["gain_chargeable_now"] == approx(50000.0)
        assert result["gain_rolled_over"] == approx(150000.0)
        assert result["cgt_without_relief"] == approx(47280.0)
        assert result["cgt_with_relief"] == approx(11280.0)
        assert result["tax_deferred"] == approx(36000.0)
        assert result["replacement_base_cost_reduction"] == approx(150000.0)

    def test_full_reinvestment_defers_the_whole_gain(self):
        # All 300,000 of proceeds reinvested: nothing chargeable now, the
        # whole 100,000 gain rolls into the new asset's base cost. Without
        # relief the charge would have been (100,000 - 3,000) x 24% = 23,280.
        result = strategy_cgt_rollover_relief(
            {"disposal_proceeds": 300000, "disposal_gain": 100000,
             "replacement_cost": 300000, "earned_income": 60000},
            TAX_YEAR,
        )
        assert result["gain_chargeable_now"] == approx(0.0)
        assert result["gain_rolled_over"] == approx(100000.0)
        assert result["cgt_with_relief"] == approx(0.0)
        assert result["tax_deferred"] == approx(23280.0)

    def test_basic_rate_composition_uses_the_18_percent_rate(self):
        # Earned 20,000 -> taxable 7,430, basic band remaining 30,270.
        # Proceeds 60,000, gain 30,000, replacement 40,000: 20,000 chargeable
        # now. Without relief (30,000 - 3,000) = 27,000, all within the band
        # at 18% = 4,860; with relief (20,000 - 3,000) x 18% = 3,060 —
        # 1,800 deferred.
        result = strategy_cgt_rollover_relief(
            {"disposal_proceeds": 60000, "disposal_gain": 30000,
             "replacement_cost": 40000, "earned_income": 20000},
            TAX_YEAR,
        )
        assert result["cgt_without_relief"] == approx(4860.0)
        assert result["cgt_with_relief"] == approx(3060.0)
        assert result["tax_deferred"] == approx(1800.0)


class TestFullExpensing:
    def test_spend_above_the_aia_cap_gets_100_percent(self):
        # 1,500,000 of new main-rate plant: 100% FYA = 1,500,000, saving
        # 375,000 at 25%. The AIA route would have relieved 1,000,000 +
        # 18% x 500,000 = 1,090,000 — full expensing adds 410,000 of
        # year-one allowance, worth 102,500.
        result = strategy_capital_allowances_full_expensing(
            {"new_main_rate_spend": 1500000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["first_year_allowance"] == approx(1500000.0)
        assert result["tax_saved_year_one"] == approx(375000.0)
        assert result["allowance_via_aia_route"] == approx(1090000.0)
        assert result["extra_first_year_allowance"] == approx(410000.0)
        assert result["extra_tax_saved_year_one"] == approx(102500.0)

    def test_spend_within_the_aia_gains_nothing_extra(self):
        # 800,000 is within the 1,000,000 AIA, so both routes fully relieve
        # it in year one: the FYA matters only above the cap.
        result = strategy_capital_allowances_full_expensing(
            {"new_main_rate_spend": 800000, "marginal_rate": 0.25}, TAX_YEAR
        )
        assert result["first_year_allowance"] == approx(800000.0)
        assert result["extra_first_year_allowance"] == approx(0.0)
        assert result["extra_tax_saved_year_one"] == approx(0.0)

    def test_marginal_rate_defaults_to_ct_main_rate(self):
        # No marginal_rate fact -> the seeded 25% main rate applies.
        result = strategy_capital_allowances_full_expensing(
            {"new_main_rate_spend": 100000}, TAX_YEAR
        )
        assert result["marginal_rate"] == approx(0.25)
        assert result["tax_saved_year_one"] == approx(25000.0)


class TestHoldingCompanyStructuring:
    def test_higher_rate_owner_defers_dividend_tax_and_taper(self):
        # Earned 60,000; extracting 50,000 as dividends now would raise ANI
        # to 110,000, tapering the PA by 5,000 (2,000 extra tax on earned)
        # and charging the dividends at 33.75% less the 500 allowance
        # (16,875 - 168.75 = 16,706.25): 18,706.25 deferred by retention.
        result = strategy_holding_company_structuring(
            {"retained_amount": 50000, "earned_income": 60000}, TAX_YEAR
        )
        assert result["personal_tax_if_extracted_now"] == approx(18706.25)
        assert result["tax_deferred_by_retention"] == approx(18706.25)
        assert result["personal_allowance_lost_if_extracted"] == approx(5000.0)
        assert result["intercompany_dividend_tax"] == approx(0.0)

    def test_basic_rate_owner_defers_the_ordinary_rate(self):
        # Earned 20,000 (taxable 7,430); 10,000 of dividends would all fall
        # in the basic band at 8.75% less the 500 allowance relief:
        # 875.00 - 43.75 = 831.25 deferred. No PA taper this far down.
        result = strategy_holding_company_structuring(
            {"retained_amount": 10000, "earned_income": 20000}, TAX_YEAR
        )
        assert result["personal_tax_if_extracted_now"] == approx(831.25)
        assert result["personal_allowance_lost_if_extracted"] == approx(0.0)

    def test_retention_on_top_of_existing_dividends(self):
        # Earned 12,570 (exactly the PA) + existing dividends 37,700 fill
        # the basic band precisely. A further 10,000 retained-or-extracted
        # would all be charged at the 33.75% upper rate = 3,375.00 (the 500
        # allowance is already used by the existing dividends).
        result = strategy_holding_company_structuring(
            {"retained_amount": 10000, "earned_income": 12570,
             "dividend_income": 37700},
            TAX_YEAR,
        )
        assert result["personal_tax_if_extracted_now"] == approx(3375.0)


class TestSdltMixedUse:
    def test_additional_dwelling_purchase_reclassified(self):
        # 800,000 as residential + 5% surcharge: banded 125,000 x 0 +
        # 125,000 x 2% (2,500) + 550,000 x 5% (27,500) = 30,000, plus
        # 40,000 surcharge = 70,000. As mixed-use (Table B): 100,000 x 2%
        # + 550,000 x 5% = 29,500. Saving 40,500.
        result = strategy_sdlt_mixed_use_classification(
            {"price": 800000, "additional_dwelling": True}, TAX_YEAR
        )
        assert result["residential_treatment"]["total_sdlt"] == approx(70000.0)
        assert result["mixed_use_sdlt"] == approx(29500.0)
        assert result["saving_if_mixed_use"] == approx(40500.0)

    def test_main_residence_purchase_still_saves_at_scale(self):
        # 2,000,000 with no surcharge: residential 0 + 2,500 + 33,750
        # (675,000 x 5%) + 57,500 (575,000 x 10%) + 60,000 (500,000 x 12%)
        # = 153,750. Table B: 2,000 + 87,500 (1,750,000 x 5%) = 89,500.
        # Saving 64,250.
        result = strategy_sdlt_mixed_use_classification(
            {"price": 2000000, "additional_dwelling": False}, TAX_YEAR
        )
        assert result["residential_treatment"]["total_sdlt"] == approx(153750.0)
        assert result["mixed_use_sdlt"] == approx(89500.0)
        assert result["saving_if_mixed_use"] == approx(64250.0)

    def test_small_purchase_can_favour_residential(self):
        # 140,000, no surcharge: residential 15,000 x 2% above 125,000 =
        # 300; Table B: 0 (below the 150,000 nil band) — mixed-use still
        # cheaper here (300 saved), but the calculator reports whatever the
        # difference is rather than assuming a saving.
        result = strategy_sdlt_mixed_use_classification(
            {"price": 140000, "additional_dwelling": False}, TAX_YEAR
        )
        assert result["residential_treatment"]["total_sdlt"] == approx(300.0)
        assert result["mixed_use_sdlt"] == approx(0.0)
        assert result["saving_if_mixed_use"] == approx(300.0)


class TestSdltUninhabitable:
    def test_derelict_additional_dwelling_reclassified(self):
        # 700,000 as residential + 5% surcharge: banded 0 + 125,000 x 2%
        # (2,500) + 450,000 x 5% (22,500) = 25,000, plus 35,000 surcharge
        # = 60,000. As non-residential (s.116 / Bewley): 100,000 x 2% +
        # 450,000 x 5% = 24,500. Saving 35,500.
        result = strategy_sdlt_uninhabitable_classification(
            {"price": 700000, "additional_dwelling": True}, TAX_YEAR
        )
        assert result["residential_treatment"]["total_sdlt"] == approx(60000.0)
        assert result["non_residential_sdlt"] == approx(24500.0)
        assert result["saving_if_non_residential"] == approx(35500.0)

    def test_single_derelict_home_no_surcharge(self):
        # 400,000, no surcharge: residential 0 + 2,500 + 150,000 x 5%
        # (7,500) = 10,000. Non-residential: 250,000 x 2%... i.e. 150,000
        # nil, 100,000 x 2% (2,000) + 150,000 x 5% (7,500) = 9,500.
        # Saving 500 — small at this level, which is honest: the relief
        # bites hardest with a surcharge or a high price.
        result = strategy_sdlt_uninhabitable_classification(
            {"price": 400000, "additional_dwelling": False}, TAX_YEAR
        )
        assert result["residential_treatment"]["total_sdlt"] == approx(10000.0)
        assert result["non_residential_sdlt"] == approx(9500.0)
        assert result["saving_if_non_residential"] == approx(500.0)


class TestFhlAbolitionTransition:
    def test_mortgaged_higher_rate_former_fhl(self):
        # Rental profit 20,000 (24,000 - 4,000) on 55,000 salary. Interest
        # 12,000 would save 40% = 4,800 under the old FHL full deduction,
        # but only a 20% reducer = 2,400 under s.24, so abolition costs
        # 2,400 extra income tax a year. Tax under s.24 = 17,432 - 2,400 =
        # 15,032; had it stayed an FHL, tax on 63,000 = 12,632.
        result = strategy_fhl_abolition_transition(
            {"rental_income": 24000, "allowable_expenses": 4000,
             "finance_costs": 12000, "other_income": 55000,
             "capital_allowances_pool_bf": 10000},
            TAX_YEAR,
        )
        assert result["extra_income_tax_from_s24"] == approx(2400.0)
        assert result["tax_under_s24"] == approx(15032.0)
        assert result["tax_if_still_fhl"] == approx(12632.0)
        assert result["writing_down_allowance_still_available"] == approx(1800.0)
        assert result["new_furnishings_allowances_lost"] is True

    def test_basic_rate_former_fhl_unaffected_by_s24(self):
        # A basic-rate landlord: rental profit 8,000 on 20,000 salary,
        # interest 3,000. Both routes relieve at 20%, so s.24 costs nothing
        # extra — the abolition's income-tax sting is a higher-rate effect.
        result = strategy_fhl_abolition_transition(
            {"rental_income": 12000, "allowable_expenses": 4000,
             "finance_costs": 3000, "other_income": 20000,
             "capital_allowances_pool_bf": 0},
            TAX_YEAR,
        )
        assert result["extra_income_tax_from_s24"] == approx(0.0)
        assert result["writing_down_allowance_still_available"] == approx(0.0)
