"""Hand-verified worked examples against the published 2025/26 rates,
independent of the seeded GoldenTestCase rows (see test_golden_cases.py) so
correctness isn't checked only against numbers this same codebase invented.
"""

import pytest

from ruleengine.calculators import (
    corporation_tax,
    dividend_tax,
    employee_class1_nic,
    employer_class1_nic,
    income_tax_on_earned_income,
    strategy_marriage_allowance_transfer,
)

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"


def test_income_tax_basic_rate_only():
    result = income_tax_on_earned_income({"total_income": 50000}, TAX_YEAR)
    assert result["personal_allowance"] == 12570
    assert result["taxable_income"] == 37430
    assert result["tax_due"] == 7486.0


def test_income_tax_personal_allowance_fully_tapered():
    result = income_tax_on_earned_income({"total_income": 130000}, TAX_YEAR)
    assert result["personal_allowance"] == 0
    assert result["tax_due"] == 44703.0


def test_income_tax_personal_allowance_partially_tapered():
    # 110000 - 100000 = 10000 excess * 0.5 = 5000 reduction -> PA = 7570
    result = income_tax_on_earned_income({"total_income": 110000}, TAX_YEAR)
    assert result["personal_allowance"] == 7570


def test_dividend_tax_allowance_within_basic_band():
    result = dividend_tax({"other_taxable_income": 30000, "dividend_income": 20000}, TAX_YEAR)
    assert result["tax_due"] == 4781.25


def test_dividend_tax_no_other_income():
    # First 500 at 0%, remaining 4500 at basic dividend rate 8.75%
    result = dividend_tax({"other_taxable_income": 0, "dividend_income": 5000}, TAX_YEAR)
    assert result["tax_due"] == pytest.approx(4500 * 0.0875)


def test_employee_class1_nic_above_uel():
    result = employee_class1_nic({"annual_salary": 60000}, TAX_YEAR)
    assert result["nic_due"] == 3210.6


def test_employee_class1_nic_below_primary_threshold():
    result = employee_class1_nic({"annual_salary": 9000}, TAX_YEAR)
    assert result["nic_due"] == 0.0


def test_employer_class1_nic_2025_26_rate():
    result = employer_class1_nic(
        {"annual_salary": 60000, "employment_allowance_available": False}, TAX_YEAR
    )
    assert result["nic_due"] == 8250.0


def test_employer_class1_nic_with_employment_allowance():
    result = employer_class1_nic(
        {"annual_salary": 60000, "employment_allowance_available": True}, TAX_YEAR
    )
    assert result["employment_allowance_relief"] == 8250.0
    assert result["nic_due"] == 0.0


def test_corporation_tax_marginal_relief_band():
    result = corporation_tax({"taxable_profit": 100000}, TAX_YEAR)
    assert result["marginal_relief"] == 2250.0
    assert result["tax_due"] == 22750.0
    assert result["effective_rate"] == pytest.approx(0.2275)


def test_corporation_tax_small_profits_rate():
    result = corporation_tax({"taxable_profit": 30000}, TAX_YEAR)
    assert result["tax_due"] == pytest.approx(30000 * 0.19)
    assert result["marginal_relief"] == 0.0


def test_corporation_tax_main_rate():
    result = corporation_tax({"taxable_profit": 300000}, TAX_YEAR)
    assert result["tax_due"] == pytest.approx(300000 * 0.25)


def test_marriage_allowance_eligible():
    result = strategy_marriage_allowance_transfer(
        {"transferor_income": 8000, "transferee_income": 30000}, TAX_YEAR
    )
    assert result["eligible"] is True
    assert result["estimated_annual_tax_saving"] == 252.0


def test_marriage_allowance_ineligible_transferor_over_pa():
    result = strategy_marriage_allowance_transfer(
        {"transferor_income": 20000, "transferee_income": 30000}, TAX_YEAR
    )
    assert result["eligible"] is False
    assert result["estimated_annual_tax_saving"] == 0.0
