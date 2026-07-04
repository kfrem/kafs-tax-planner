"""IHT module tests: estate liability calculator and the three planning
strategies. All expected values hand-computed from IHTA 1984 rates as
frozen through 2029/30 (NRB 325,000 / RNRB 175,000, taper at 2m).
"""

import pytest

from ruleengine.calculators import (
    iht_estate_liability,
    strategy_iht_charitable_legacy,
    strategy_iht_lifetime_gifting,
    strategy_iht_spousal_nil_rate_bands,
)

pytestmark = pytest.mark.usefixtures("seeded_rule_base")

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731


class TestEstateLiability:
    def test_nrb_and_rnrb_shelter_estate(self):
        result = iht_estate_liability(
            {
                "gross_estate_value": 800000,
                "home_equity_value": 300000,
                "home_passes_to_direct_descendants": True,
            },
            TAX_YEAR,
        )
        assert result["taxable_amount"] == approx(300000.0)
        assert result["tax_due"] == approx(120000.0)

    def test_rnrb_capped_at_home_equity(self):
        # Home equity 120,000 < 175,000 RNRB: only 120,000 available.
        result = iht_estate_liability(
            {
                "gross_estate_value": 700000,
                "home_equity_value": 120000,
                "home_passes_to_direct_descendants": True,
            },
            TAX_YEAR,
        )
        assert result["residence_nil_rate_band"] == approx(120000.0)
        assert result["tax_due"] == approx((700000 - 325000 - 120000) * 0.40)

    def test_no_rnrb_if_home_not_to_descendants(self):
        result = iht_estate_liability(
            {
                "gross_estate_value": 700000,
                "home_equity_value": 300000,
                "home_passes_to_direct_descendants": False,
            },
            TAX_YEAR,
        )
        assert result["residence_nil_rate_band"] == 0.0
        assert result["tax_due"] == approx(150000.0)

    def test_rnrb_taper_above_2m(self):
        result = iht_estate_liability(
            {
                "gross_estate_value": 2200000,
                "home_equity_value": 400000,
                "home_passes_to_direct_descendants": True,
            },
            TAX_YEAR,
        )
        assert result["residence_nil_rate_band"] == approx(75000.0)
        assert result["tax_due"] == approx(720000.0)

    def test_spouse_exemption_removes_charge(self):
        result = iht_estate_liability(
            {"gross_estate_value": 1000000, "amount_to_spouse": 1000000},
            TAX_YEAR,
        )
        assert result["tax_due"] == 0.0

    def test_charity_ten_percent_gets_reduced_rate(self):
        result = iht_estate_liability(
            {"gross_estate_value": 1000000, "charitable_legacy": 67500},
            TAX_YEAR,
        )
        assert result["qualifies_reduced_charity_rate"] is True
        assert result["tax_due"] == approx(218700.0)

    def test_charity_below_ten_percent_stays_at_40(self):
        result = iht_estate_liability(
            {"gross_estate_value": 1000000, "charitable_legacy": 50000},
            TAX_YEAR,
        )
        assert result["qualifies_reduced_charity_rate"] is False
        assert result["rate_applied"] == 0.40


class TestSpousalTransferStrategy:
    def test_sarah_household_position(self):
        # Combined second-death estate 1,900,000, home equity 600,000 to
        # children. With claims: NRB 650,000 + RNRB 350,000 -> taxable
        # 900,000 -> 360,000. Without claims: 325,000 + 175,000 -> taxable
        # 1,400,000 -> 560,000. The claims are worth 200,000
        # (40% of the 500,000 of transferred bands).
        result = strategy_iht_spousal_nil_rate_bands(
            {
                "combined_estate_second_death": 1900000,
                "combined_home_equity_second_death": 600000,
                "home_passes_to_direct_descendants": True,
            },
            TAX_YEAR,
        )
        assert result["first_death_tax_with_full_spouse_exemption"] == 0.0
        assert result["second_death_with_transferred_bands"]["tax_due"] == approx(360000.0)
        assert result["second_death_without_claims"]["tax_due"] == approx(560000.0)
        assert result["value_of_transferable_bands"] == approx(200000.0)
        assert result["rnrb_taper_applies"] is False


class TestLifetimeGiftingStrategy:
    def test_gift_with_exemptions_and_seven_year_saving(self):
        # 100,000 gift from the 1,900,000 combined estate (full transferred
        # bands): 6,000 immediately exempt (current + unused prior year),
        # PET 94,000. Surviving 7 years: tax falls 360,000 -> 320,000.
        result = strategy_iht_lifetime_gifting(
            {
                "planned_gift": 100000,
                "estate_basis_value": 1900000,
                "home_equity_value": 600000,
                "home_passes_to_direct_descendants": True,
                "transferred_nrb_fraction": 1,
                "transferred_rnrb_fraction": 1,
                "prior_year_annual_exemption_unused": True,
            },
            TAX_YEAR,
        )
        assert result["immediately_exempt_amount"] == approx(6000.0)
        assert result["pet_amount"] == approx(94000.0)
        assert result["estate_tax_before_gift"] == approx(360000.0)
        assert result["estate_tax_if_survive_7_years"] == approx(320000.0)
        assert result["saving_if_survive_7_years"] == approx(40000.0)

    def test_gift_can_restore_tapered_rnrb(self):
        # Estate 2,100,000 (home 400,000 to children): RNRB tapered by
        # 50,000 to 125,000 -> taxable 1,650,000 -> 660,000. A 100,000 gift
        # brings the estate to 2,000,000, restoring the full RNRB: taxable
        # 1,500,000 -> 600,000. Saving 60,000 on a 100,000 gift (60%
        # effective relief in the taper zone).
        result = strategy_iht_lifetime_gifting(
            {
                "planned_gift": 100000,
                "estate_basis_value": 2100000,
                "home_equity_value": 400000,
                "home_passes_to_direct_descendants": True,
            },
            TAX_YEAR,
        )
        assert result["estate_tax_before_gift"] == approx(660000.0)
        assert result["estate_tax_if_survive_7_years"] == approx(600000.0)
        assert result["saving_if_survive_7_years"] == approx(60000.0)


class TestCharitableLegacyStrategy:
    def test_topping_up_to_ten_percent(self):
        # Sarah household basis: baseline 1,900,000 - 650,000 = 1,250,000;
        # target legacy 125,000. Tax falls 360,000 -> 279,000 (36% on
        # 775,000). Net cost to beneficiaries: 125,000 - 81,000 = 44,000.
        result = strategy_iht_charitable_legacy(
            {
                "estate_basis_value": 1900000,
                "home_equity_value": 600000,
                "home_passes_to_direct_descendants": True,
                "transferred_nrb_fraction": 1,
                "transferred_rnrb_fraction": 1,
                "current_charitable_legacy": 0,
            },
            TAX_YEAR,
        )
        assert result["already_qualifies"] is False
        assert result["target_legacy_for_reduced_rate"] == approx(125000.0)
        assert result["position_at_target_legacy"]["tax_due"] == approx(279000.0)
        assert result["tax_saving"] == approx(81000.0)
        assert result["net_cost_to_beneficiaries"] == approx(44000.0)

    def test_already_qualifying_estate(self):
        result = strategy_iht_charitable_legacy(
            {"estate_basis_value": 1000000, "current_charitable_legacy": 70000},
            TAX_YEAR,
        )
        assert result["already_qualifies"] is True
