"""Adapter mapping tests: the fact-schema fields must reach the right
calculator inputs. Added with the employment_income field (a PAYE job at
a third-party employer), which counts as earned income everywhere and —
unlike 'other income' — as relevant UK earnings for pension relief.
"""

from advice.strategy_adapters import ADAPTERS

FACTS = {
    "personal": {
        "other_income": 1000,        # e.g. rent: earned for banding, NOT relevant earnings
        "employment_income": 20000,  # PAYE job: earned AND relevant earnings
        "salary_from_own_company": 5000,
        "dividends_from_own_company": 2000,
        "spouse_income": 15000,
    },
    "company": {"profit_before_remuneration": 50000},
    "sole_trade": {"annual_profit": 10000},
    "pension": {"desired_contribution": 8000, "unused_aa_prior_3_years": [0, 0, 0]},
    "estate": {},
    "property": {
        "disposal_gain": 30000,
        "disposal_asset_type": "residential",
        "ownership_months": 60,
        "occupied_as_main_residence_months": 30,
        "spouse_available_for_transfer": True,
    },
}


def test_mix_includes_employment_income():
    calc_facts = ADAPTERS["strategy.salary_dividend_mix"].to_facts(FACTS)
    # 1,000 other + 20,000 employment + 10,000 sole trade
    assert calc_facts["other_personal_income"] == 31000


def test_incorporation_includes_employment_income():
    calc_facts = ADAPTERS["strategy.incorporation_vs_sole_trade"].to_facts(FACTS)
    # 1,000 other + 20,000 employment + 5,000 own-company salary
    assert calc_facts["other_personal_income"] == 26000


def test_pension_relevant_earnings_include_employment_but_not_other():
    calc_facts = ADAPTERS["strategy.pension_annual_allowance_carry_forward"].to_facts(FACTS)
    # 5,000 salary + 10,000 sole trade + 20,000 employment; rent excluded
    assert calc_facts["relevant_uk_earnings"] == 35000
    # earned income for the tax computation additionally includes the rent
    assert calc_facts["earned_income"] == 36000


def test_marriage_allowance_transferor_includes_employment():
    calc_facts = ADAPTERS["strategy.marriage_allowance_transfer"].to_facts(FACTS)
    # 1,000 + 20,000 + 5,000 + 2,000 dividends + 10,000 sole trade
    assert calc_facts["transferor_income"] == 38000


def test_cgt_adapters_include_employment():
    ppr = ADAPTERS["strategy.cgt_ppr_relief"].to_facts(FACTS)
    spousal = ADAPTERS["strategy.cgt_spousal_transfer_before_disposal"].to_facts(FACTS)
    # 20,000 employment + 1,000 other + 5,000 salary + 10,000 sole trade
    assert ppr["earned_income"] == 36000
    assert spousal["earned_income"] == 36000
