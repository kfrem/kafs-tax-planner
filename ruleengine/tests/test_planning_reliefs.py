"""Tier-1 planning strategies (see docs/TAX_PLANNING_COVERAGE.md). All
expected values hand-computed from published 2025/26 rates, with the working
shown in the comment."""

import pytest

from ruleengine.calculators import strategy_gift_aid_relief

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
