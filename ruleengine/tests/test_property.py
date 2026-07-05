"""Property/CGT module tests: CGT rate banding, private residence relief
with the final-9-months rule, spousal transfer before disposal, and SDLT
including the additional-dwellings surcharge and first-time buyers'
relief. All expected values hand-computed from published 2025/26 rates.
"""

import pytest

from ruleengine.calculators import (
    cgt_liability,
    sdlt_residential,
    strategy_cgt_business_asset_disposal_relief,
    strategy_cgt_ppr_relief,
    strategy_cgt_spousal_transfer,
    strategy_sdlt_purchase,
)

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731


class TestCgtLiability:
    def test_gain_straddles_basic_band(self):
        # Earned 42,270 -> taxable income 29,700 -> 8,000 of basic band
        # left. Gain 15,000 - 3,000 AEA = 12,000: 8,000 @ 18% + 4,000 @ 24%.
        result = cgt_liability(
            {"chargeable_gain": 15000, "asset_type": "residential", "earned_income": 42270},
            TAX_YEAR,
        )
        assert result["gain_at_lower_rate"] == approx(8000.0)
        assert result["gain_at_higher_rate"] == approx(4000.0)
        assert result["tax_due"] == approx(2400.0)

    def test_higher_rate_taxpayer_all_at_24(self):
        # Earned 115,000: taxable income far above the basic-rate limit.
        # 150,000 - 3,000 = 147,000 all at 24% = 35,280.
        result = cgt_liability(
            {"chargeable_gain": 150000, "asset_type": "residential", "earned_income": 115000},
            TAX_YEAR,
        )
        assert result["tax_due"] == approx(35280.0)

    def test_gain_within_annual_exempt_amount(self):
        result = cgt_liability(
            {"chargeable_gain": 2500, "asset_type": "other", "earned_income": 50000},
            TAX_YEAR,
        )
        assert result["taxable_gain"] == 0.0
        assert result["tax_due"] == 0.0


class TestPprRelief:
    def test_partial_occupation_with_final_period(self):
        # Owned 120 months, occupied 60: exempt (60 + 9)/120 = 57.5% of the
        # 120,000 gain -> 69,000 exempt, 51,000 chargeable, less 3,000 AEA
        # = 48,000. Earned 30,000 -> 20,270 basic band left:
        # 20,270 @ 18% (3,648.60) + 27,730 @ 24% (6,655.20) = 10,303.80.
        result = strategy_cgt_ppr_relief(
            {
                "disposal_gain": 120000,
                "ownership_months": 120,
                "occupied_as_main_residence_months": 60,
                "earned_income": 30000,
            },
            TAX_YEAR,
        )
        assert result["exempt_months_including_final_period"] == approx(69.0)
        assert result["exempt_gain"] == approx(69000.0)
        assert result["cgt_with_relief"] == approx(10303.80)
        assert result["relief_saving"] == approx(16560.0)

    def test_full_occupation_fully_exempt(self):
        result = strategy_cgt_ppr_relief(
            {
                "disposal_gain": 200000,
                "ownership_months": 96,
                "occupied_as_main_residence_months": 96,
                "earned_income": 60000,
            },
            TAX_YEAR,
        )
        assert result["exempt_gain"] == approx(200000.0)
        assert result["cgt_with_relief"] == 0.0


class TestSpousalTransfer:
    def test_both_higher_rate_saves_only_second_aea(self):
        # Victor's case: both spouses higher-rate. Alone: 147,000 @ 24% =
        # 35,280. Split: each (75,000 - 3,000) @ 24% = 17,280 -> 34,560.
        # Honest answer: the play is worth exactly 720 (the second AEA).
        result = strategy_cgt_spousal_transfer(
            {
                "disposal_gain": 150000,
                "asset_type": "residential",
                "earned_income": 115000,
                "spouse_earned_income": 110000,
            },
            TAX_YEAR,
        )
        assert result["cgt_disposing_alone"] == approx(35280.0)
        assert result["cgt_after_half_share_to_spouse"] == approx(34560.0)
        assert result["saving"] == approx(720.0)

    def test_basic_rate_spouse_saves_band_as_well(self):
        # Spouse earning 20,000 has taxable income 7,430 -> 30,270 of basic
        # band left; their 72,000 taxable half: 30,270 @ 18% (5,448.60) +
        # 41,730 @ 24% (10,015.20) = 15,463.80 vs 17,280 at 24% flat.
        # Total split = 17,280 + 15,463.80 = 32,743.80; saving 2,536.20.
        result = strategy_cgt_spousal_transfer(
            {
                "disposal_gain": 150000,
                "asset_type": "residential",
                "earned_income": 115000,
                "spouse_earned_income": 20000,
            },
            TAX_YEAR,
        )
        assert result["spouse_half_cgt"] == approx(15463.80)
        assert result["saving"] == approx(2536.20)


class TestBadr:
    def test_qualifying_gain_within_lifetime_limit(self):
        # Gain 500,000 - 3,000 AEA = 497,000, all within the 1m limit at 14%
        # = 69,580. Without relief: earned 60,000 -> taxable income 47,430,
        # above the 37,700 basic limit, so all 497,000 at 24% = 119,280.
        # Saving 49,700.
        result = strategy_cgt_business_asset_disposal_relief(
            {"disposal_gain": 500000, "earned_income": 60000}, TAX_YEAR
        )
        assert result["gain_at_badr_rate"] == approx(497000.0)
        assert result["cgt_with_badr"] == approx(69580.0)
        assert result["cgt_without_badr"] == approx(119280.0)
        assert result["saving"] == approx(49700.0)

    def test_gain_above_lifetime_limit_excess_at_standard_rate(self):
        # Gain 1,200,000 - 3,000 AEA = 1,197,000. First 1,000,000 at 14% =
        # 140,000; excess 197,000 at 24% = 47,280; total 187,280. Without
        # relief 1,197,000 at 24% = 287,280. Saving 100,000 (1m x 10 pts).
        result = strategy_cgt_business_asset_disposal_relief(
            {"disposal_gain": 1200000, "earned_income": 60000}, TAX_YEAR
        )
        assert result["gain_at_badr_rate"] == approx(1000000.0)
        assert result["gain_above_lifetime_limit"] == approx(197000.0)
        assert result["cgt_with_badr"] == approx(187280.0)
        assert result["saving"] == approx(100000.0)

    def test_prior_claims_reduce_remaining_limit(self):
        # 700,000 of the 1m limit already used -> 300,000 remains. Gain
        # 600,000 - 3,000 AEA = 597,000: 300,000 at 14% (42,000) + 297,000 at
        # 24% (71,280) = 113,280. Without relief 597,000 at 24% = 143,280.
        # Saving 30,000 (300,000 x 10 pts).
        result = strategy_cgt_business_asset_disposal_relief(
            {
                "disposal_gain": 600000,
                "earned_income": 60000,
                "badr_lifetime_limit_used": 700000,
            },
            TAX_YEAR,
        )
        assert result["remaining_lifetime_limit"] == approx(300000.0)
        assert result["gain_at_badr_rate"] == approx(300000.0)
        assert result["cgt_with_badr"] == approx(113280.0)
        assert result["saving"] == approx(30000.0)


class TestSdlt:
    def test_standard_purchase(self):
        result = sdlt_residential({"price": 350000}, TAX_YEAR)
        assert result["total_sdlt"] == approx(7500.0)

    def test_additional_dwelling_surcharge(self):
        result = sdlt_residential({"price": 350000, "additional_dwelling": True}, TAX_YEAR)
        assert result["additional_dwelling_surcharge"] == approx(17500.0)
        assert result["total_sdlt"] == approx(25000.0)

    def test_first_time_buyer_relief(self):
        # 350,000 FTB: 0 up to 300,000, 5% on the next 50,000 = 2,500.
        result = sdlt_residential({"price": 350000, "first_time_buyer": True}, TAX_YEAR)
        assert result["first_time_buyer_relief_applied"] is True
        assert result["total_sdlt"] == approx(2500.0)

    def test_ftb_relief_lost_above_cap(self):
        # 550,000 exceeds the 500,000 cap: standard bands apply ->
        # 2,500 + 15,000 = 17,500.
        result = sdlt_residential({"price": 550000, "first_time_buyer": True}, TAX_YEAR)
        assert result["first_time_buyer_relief_applied"] is False
        assert result["total_sdlt"] == approx(17500.0)

    def test_purchase_strategy_isolates_surcharge_cost(self):
        result = strategy_sdlt_purchase(
            {"price": 350000, "additional_dwelling": True}, TAX_YEAR
        )
        assert result["surcharge_cost_of_additional_dwelling"] == approx(17500.0)
        assert result["as_planned"]["total_sdlt"] == approx(25000.0)
