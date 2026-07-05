"""Property/CGT module tests: CGT rate banding, private residence relief
with the final-9-months rule, spousal transfer before disposal, and SDLT
including the additional-dwellings surcharge and first-time buyers'
relief. All expected values hand-computed from published 2025/26 rates.
"""

import pytest

from ruleengine.engine import get_parameter
from ruleengine.calculators import (
    cgt_liability,
    lbtt_residential,
    ltt_residential,
    sdlt_residential,
    strategy_cgt_business_asset_disposal_relief,
    strategy_cgt_lettings_relief,
    strategy_cgt_ppr_relief,
    strategy_cgt_spousal_transfer,
    strategy_lbtt_non_residential_purchase,
    strategy_lbtt_purchase,
    strategy_ltt_non_residential_purchase,
    strategy_ltt_purchase,
    strategy_sdlt_non_residential_purchase,
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


class TestLettingsRelief:
    def test_hs283_shared_occupancy_example(self):
        # HMRC HS283: gain 60,000, 40% owner-occupied / 60% let. PPR = 40% =
        # 24,000; letting gain = 60% = 36,000; lettings relief = lowest of
        # (36,000, 24,000, 40,000) = 24,000; chargeable 36,000 - 24,000 =
        # 12,000; less 3,000 AEA = 9,000 @ 24% (earned 60,000 fills the band)
        # = 2,160. Without lettings relief: 36,000 - 3,000 = 33,000 @ 24% =
        # 7,920, so the relief saves 5,760.
        result = strategy_cgt_lettings_relief(
            {"disposal_gain": 60000, "let_fraction": 0.60, "earned_income": 60000}, TAX_YEAR
        )
        assert result["private_residence_relief"] == approx(24000.0)
        assert result["letting_gain"] == approx(36000.0)
        assert result["lettings_relief"] == approx(24000.0)
        assert result["chargeable_gain_after_reliefs"] == approx(12000.0)
        assert result["cgt_due"] == approx(2160.0)
        assert result["lettings_relief_tax_saving"] == approx(5760.0)

    def test_40000_cap_binds(self):
        # Gain 200,000, 50/50. PPR = 100,000; letting gain = 100,000;
        # lettings relief = lowest of (100,000, 100,000, 40,000) = 40,000
        # (the cap binds); chargeable 100,000 - 40,000 = 60,000; less 3,000
        # AEA = 57,000 @ 24% = 13,680.
        result = strategy_cgt_lettings_relief(
            {"disposal_gain": 200000, "let_fraction": 0.50, "earned_income": 60000}, TAX_YEAR
        )
        assert result["lettings_relief"] == approx(40000.0)
        assert result["chargeable_gain_after_reliefs"] == approx(60000.0)
        assert result["cgt_due"] == approx(13680.0)

    def test_ppr_relief_is_the_binding_minimum(self):
        # Gain 100,000, 90% let / 10% occupied. PPR = 10,000; letting gain =
        # 90,000; lettings relief = lowest of (90,000, 10,000, 40,000) =
        # 10,000 (PPR binds); chargeable 90,000 - 10,000 = 80,000; less 3,000
        # AEA = 77,000 @ 24% = 18,480.
        result = strategy_cgt_lettings_relief(
            {"disposal_gain": 100000, "let_fraction": 0.90, "earned_income": 60000}, TAX_YEAR
        )
        assert result["lettings_relief"] == approx(10000.0)
        assert result["chargeable_gain_after_reliefs"] == approx(80000.0)
        assert result["cgt_due"] == approx(18480.0)


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


class TestLbtt:
    def test_standard_purchase(self):
        # Scotland, 350,000: 145,000 @ 0% + 105,000 @ 2% (2,100) + 75,000 @
        # 5% (3,750) + 25,000 @ 10% (2,500) = 8,350. (SDLT on the same price
        # is 7,500 — the devolved charge genuinely differs.)
        result = lbtt_residential({"price": 350000}, TAX_YEAR)
        assert result["banded_lbtt"] == approx(8350.0)
        assert result["total_lbtt"] == approx(8350.0)

    def test_first_time_buyer_relief_worth_600(self):
        # FTB nil band raised to 175,000. At 200,000: 175,000 @ 0% + 25,000 @
        # 2% = 500. Without relief: 145,000 @ 0% + 55,000 @ 2% = 1,100.
        # Relief worth 600.
        relieved = lbtt_residential({"price": 200000, "first_time_buyer": True}, TAX_YEAR)
        normal = lbtt_residential({"price": 200000}, TAX_YEAR)
        assert relieved["first_time_buyer_relief_applied"] is True
        assert relieved["total_lbtt"] == approx(500.0)
        assert normal["total_lbtt"] - relieved["total_lbtt"] == approx(600.0)

    def test_additional_dwelling_supplement_on_whole_price(self):
        # ADS is 8% of the whole 350,000 = 28,000, on top of the 8,350 banded
        # charge = 36,350.
        result = lbtt_residential({"price": 350000, "additional_dwelling": True}, TAX_YEAR)
        assert result["additional_dwelling_supplement"] == approx(28000.0)
        assert result["total_lbtt"] == approx(36350.0)

    def test_purchase_strategy_isolates_supplement(self):
        result = strategy_lbtt_purchase(
            {"price": 350000, "additional_dwelling": True}, TAX_YEAR
        )
        assert result["supplement_cost_of_additional_dwelling"] == approx(28000.0)
        assert result["as_planned"]["total_lbtt"] == approx(36350.0)


class TestFutureYearBadr:
    """The 2026/27 release scaffolding: BADR's rate rises from 14% to 18%
    on 6 April 2026 (FA 2025), held as two effective-dated rows, and the
    engine resolves the right one by tax year."""

    def test_badr_parameter_is_effective_dated_across_years(self):
        # Same key, two non-overlapping rows: 14% for 2025/26, 18% from
        # 6 April 2026. The engine picks by the tax year's anchor date.
        assert get_parameter("cgt.business_asset_disposal_relief", "2025/26")["rate"] == 0.14
        assert get_parameter("cgt.business_asset_disposal_relief", "2026/27")["rate"] == 0.18

    def test_badr_rate_and_tax_flip_at_the_year_boundary(self):
        # 500,000 higher-rate disposal, 497,000 taxable after AEA. At 14% =
        # 69,580; at 18% = 89,460. The unrelieved comparison (497,000 @ 24% =
        # 119,280) is unchanged, so the 2026/27 saving falls to 29,820.
        facts = {"disposal_gain": 500000, "earned_income": 60000}
        r25 = strategy_cgt_business_asset_disposal_relief(facts, "2025/26")
        r26 = strategy_cgt_business_asset_disposal_relief(facts, "2026/27")
        assert r25["badr_rate"] == approx(0.14)
        assert r25["cgt_with_badr"] == approx(69580.0)
        assert r26["badr_rate"] == approx(0.18)
        assert r26["cgt_with_badr"] == approx(89460.0)
        assert r26["saving"] == approx(29820.0)


class TestNonResidentialLandTax:
    # A £500,000 commercial freehold, charged three different ways.
    def test_sdlt_non_residential(self):
        # England/NI: 150,000 @ 0% + 100,000 @ 2% (2,000) + 250,000 @ 5%
        # (12,500) = 14,500.
        result = strategy_sdlt_non_residential_purchase({"price": 500000}, TAX_YEAR)
        assert result["total_sdlt"] == approx(14500.0)

    def test_lbtt_non_residential(self):
        # Scotland: 150,000 @ 0% + 100,000 @ 1% (1,000) + 250,000 @ 5%
        # (12,500) = 13,500 (the 1% middle band undercuts England's 2%).
        result = strategy_lbtt_non_residential_purchase({"price": 500000}, TAX_YEAR)
        assert result["total_lbtt"] == approx(13500.0)

    def test_ltt_non_residential(self):
        # Wales: 225,000 @ 0% + 25,000 @ 1% (250) + 250,000 @ 5% (12,500) =
        # 12,750 (higher nil-rate threshold).
        result = strategy_ltt_non_residential_purchase({"price": 500000}, TAX_YEAR)
        assert result["total_ltt"] == approx(12750.0)

    def test_ltt_non_residential_top_band(self):
        # Wales at 1,500,000 exercises the 6% top band: 225,000 @ 0% + 25,000
        # @ 1% (250) + 750,000 @ 5% (37,500) + 500,000 @ 6% (30,000) = 67,750.
        result = strategy_ltt_non_residential_purchase({"price": 1500000}, TAX_YEAR)
        assert result["total_ltt"] == approx(67750.0)


class TestLtt:
    def test_main_rates_purchase(self):
        # Wales main rates, 400,000: 225,000 @ 0% + 175,000 @ 6% = 10,500.
        result = ltt_residential({"price": 400000}, TAX_YEAR)
        assert result["total_ltt"] == approx(10500.0)

    def test_higher_rates_additional_property(self):
        # Additional dwelling uses the separate higher-rate table: 180,000 @
        # 5% (9,000) + 70,000 @ 8.5% (5,950) + 150,000 @ 10% (15,000) =
        # 29,950.
        result = ltt_residential({"price": 400000, "additional_dwelling": True}, TAX_YEAR)
        assert result["total_ltt"] == approx(29950.0)

    def test_purchase_strategy_isolates_additional_property_cost(self):
        # Extra cost of buying as an additional property: 29,950 - 10,500 =
        # 19,450.
        result = strategy_ltt_purchase(
            {"price": 400000, "additional_dwelling": True}, TAX_YEAR
        )
        assert result["additional_property_cost"] == approx(19450.0)
        assert result["as_planned"]["total_ltt"] == approx(29950.0)
