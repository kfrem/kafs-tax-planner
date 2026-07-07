"""Termination-payment strategy (ITEPA 2003 ss.401-403; SSCBA 1992 s.10).

All expected values hand-computed from published 2025/26 rates, working shown.
The excess over the £30,000 exemption is taxed as the TOP SLICE of income, so
these cases deliberately cover the basic/higher-rate straddle, a wholly-exempt
payment, an entirely-higher-rate excess, and a payment large enough to strip the
personal allowance — the interaction the examiners' reports flag as commonly
missed.
"""

import pytest

from ruleengine.calculators import strategy_termination_payment

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

YEAR = "2025/26"


class TestTerminationPayment:
    def test_excess_straddles_basic_and_higher_rate(self):
        # 50,000 payment, 30,000 exempt -> 20,000 excess on top of 40,000 other
        # income. 10,270 fills the basic-rate band to 37,700 at 20% = 2,054;
        # remaining 9,730 at 40% = 3,892 -> 5,946. Employer Class 1A 20,000 @ 15%
        # = 3,000. Net = 50,000 - 5,946 = 44,054.
        r = strategy_termination_payment(
            {"termination_payment": 50000, "other_income": 40000}, YEAR
        )
        assert r["exempt_amount"] == 30000.0
        assert r["taxable_excess"] == 20000.0
        assert r["income_tax_on_excess"] == 5946.0
        assert r["employer_class1a_nic"] == 3000.0
        assert r["net_to_employee"] == 44054.0
        assert r["total_employer_cost"] == 53000.0

    def test_payment_within_the_exemption_is_tax_free(self):
        # 25,000 is below the 30,000 exemption -> wholly exempt, no tax, no NIC.
        r = strategy_termination_payment(
            {"termination_payment": 25000, "other_income": 40000}, YEAR
        )
        assert r["exempt_amount"] == 25000.0
        assert r["taxable_excess"] == 0.0
        assert r["income_tax_on_excess"] == 0.0
        assert r["employer_class1a_nic"] == 0.0
        assert r["net_to_employee"] == 25000.0

    def test_excess_entirely_in_higher_rate(self):
        # Other income 60,000 (already higher rate). 40,000 payment -> 10,000
        # excess all at 40% = 4,000. Employer Class 1A 10,000 @ 15% = 1,500.
        r = strategy_termination_payment(
            {"termination_payment": 40000, "other_income": 60000}, YEAR
        )
        assert r["taxable_excess"] == 10000.0
        assert r["income_tax_on_excess"] == 4000.0
        assert r["employer_class1a_nic"] == 1500.0
        assert r["net_to_employee"] == 36000.0

    def test_large_payment_strips_the_personal_allowance(self):
        # Other income 110,000 (PA already partly tapered to 7,570). 60,000
        # payment -> 30,000 excess taxed on top: IT(140,000) - IT(110,000).
        # IT(110,000)=33,432; IT(140,000)=49,203 (PA fully gone, some at 45%).
        # Excess tax = 15,771 -- more than a flat 40%/45%, because the payment
        # itself removes the remaining personal allowance. Employer NIC 4,500.
        r = strategy_termination_payment(
            {"termination_payment": 60000, "other_income": 110000}, YEAR
        )
        assert r["taxable_excess"] == 30000.0
        assert r["income_tax_on_excess"] == 15771.0
        assert r["employer_class1a_nic"] == 4500.0
        assert r["net_to_employee"] == 44229.0

    def test_no_payment_returns_zeroes(self):
        r = strategy_termination_payment(
            {"termination_payment": 0, "other_income": 40000}, YEAR
        )
        assert r["taxable_excess"] == 0.0
        assert r["income_tax_on_excess"] == 0.0
        assert r["net_to_employee"] == 0.0
