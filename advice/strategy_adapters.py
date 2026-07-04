"""Adapts a ClientFactSet's nested ``facts`` JSON into the flat keyword
arguments each strategy calculator expects, and decides whether a strategy
is even eligible to run for a given client's facts.

This is deliberately plain Python rather than a generic JSON rule
interpreter: with a handful of MVP strategies, an explicit mapping per
``calculator_key`` is easier for the tax editor's engineering counterpart to
audit than a condition DSL, while ``Strategy.eligibility_conditions`` still
holds the human-readable description of the condition for the record.
"""

from __future__ import annotations

from typing import Callable

ADAPTERS: dict[str, "StrategyAdapter"] = {}


def _estate_basis(facts: dict) -> dict:
    """The estate the IHT strategies plan against: the combined second-death
    estate with full transferred bands where a spouse position is recorded
    (the common married owner-manager case), otherwise the client's own
    estate with no transferred bands."""
    estate = facts.get("estate", {})
    combined = estate.get("combined_estate_second_death", 0)
    if combined > 0:
        return {
            "estate_basis_value": combined,
            "home_equity_value": estate.get("combined_home_equity_second_death", 0),
            "home_passes_to_direct_descendants": estate.get(
                "home_passes_to_direct_descendants", False
            ),
            "transferred_nrb_fraction": 1,
            "transferred_rnrb_fraction": 1,
        }
    return {
        "estate_basis_value": max(
            0, estate.get("gross_value", 0) - estate.get("liabilities", 0)
        ),
        "home_equity_value": estate.get("home_equity_value", 0),
        "home_passes_to_direct_descendants": estate.get(
            "home_passes_to_direct_descendants", False
        ),
        "transferred_nrb_fraction": estate.get("transferred_nrb_fraction", 0),
        "transferred_rnrb_fraction": estate.get("transferred_rnrb_fraction", 0),
    }


class StrategyAdapter:
    def __init__(self, calculator_key: str, is_eligible: Callable, to_facts: Callable):
        self.calculator_key = calculator_key
        self.is_eligible = is_eligible
        self.to_facts = to_facts


def adapter(calculator_key: str):
    def decorator(cls):
        ADAPTERS[calculator_key] = cls
        return cls

    return decorator


@adapter("strategy.salary_dividend_mix")
class SalaryDividendMixAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("company", {}).get("profit_before_remuneration", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        company = facts.get("company", {})
        personal = facts.get("personal", {})
        # Whole-income view: sole-trade profit and other income fill the
        # client's bands/taper before any extraction is layered on top.
        other_income = (
            personal.get("other_income", 0)
            + facts.get("sole_trade", {}).get("annual_profit", 0)
        )
        return {
            "company_profit_before_remuneration": company.get("profit_before_remuneration", 0),
            "other_personal_income": other_income,
            "employment_allowance_available": company.get("employment_allowance_available", False),
        }


@adapter("strategy.pension_annual_allowance_carry_forward")
class PensionCarryForwardAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("pension", {}).get("desired_contribution", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        personal = facts.get("personal", {})
        pension = facts.get("pension", {})
        sole_trade_profit = facts.get("sole_trade", {}).get("annual_profit", 0)
        salary = personal.get("salary_from_own_company", 0)
        # Relevant UK earnings (FA 2004 s.190): employment and trading income
        # only — dividends and 'other' income (which may be rent/savings) are
        # excluded from the personal-contribution relief cap.
        relevant_uk_earnings = salary + sole_trade_profit
        earned_income = personal.get("other_income", 0) + relevant_uk_earnings
        return {
            "desired_contribution": pension.get("desired_contribution", 0),
            "earned_income": earned_income,
            "dividend_income": personal.get("dividends_from_own_company", 0),
            "relevant_uk_earnings": relevant_uk_earnings,
            "company_profit_before_remuneration": facts.get("company", {}).get(
                "profit_before_remuneration", 0
            ),
            "threshold_income": pension.get("threshold_income", 0),
            "adjusted_income": pension.get("adjusted_income", 0),
            "unused_aa_prior_3_years": pension.get("unused_aa_prior_3_years", [0, 0, 0]),
        }


@adapter("strategy.incorporation_vs_sole_trade")
class IncorporationVsSoleTradeAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("sole_trade", {}).get("annual_profit", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        personal = facts.get("personal", {})
        # Salary already drawn from the client's own company counts as other
        # earned income in both arms of the comparison. Dividends drawn are
        # not included here because the standard fact set records planned
        # extraction, which the salary/dividend strategy itself determines.
        other_income = personal.get("other_income", 0) + personal.get(
            "salary_from_own_company", 0
        )
        return {
            "annual_profit": facts.get("sole_trade", {}).get("annual_profit", 0),
            "other_personal_income": other_income,
        }


@adapter("strategy.marriage_allowance_transfer")
class MarriageAllowanceAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        personal = facts.get("personal", {})
        return personal.get("spouse_income", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        personal = facts.get("personal", {})
        transferor_income = (
            personal.get("other_income", 0)
            + personal.get("salary_from_own_company", 0)
            + personal.get("dividends_from_own_company", 0)
            + facts.get("sole_trade", {}).get("annual_profit", 0)
        )
        return {
            "transferor_income": transferor_income,
            "transferee_income": personal.get("spouse_income", 0),
        }


def _earned_income(facts: dict) -> float:
    personal = facts.get("personal", {})
    return (
        personal.get("other_income", 0)
        + personal.get("salary_from_own_company", 0)
        + facts.get("sole_trade", {}).get("annual_profit", 0)
    )


@adapter("strategy.cgt_ppr_relief")
class CgtPprReliefAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        return (
            prop.get("disposal_gain", 0) > 0
            and prop.get("occupied_as_main_residence_months", 0) > 0
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "disposal_gain": prop.get("disposal_gain", 0),
            "ownership_months": prop.get("ownership_months", 1),
            "occupied_as_main_residence_months": prop.get("occupied_as_main_residence_months", 0),
            "earned_income": _earned_income(facts),
        }


@adapter("strategy.cgt_spousal_transfer_before_disposal")
class CgtSpousalTransferAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        return prop.get("disposal_gain", 0) > 0 and prop.get(
            "spouse_available_for_transfer", False
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "disposal_gain": prop.get("disposal_gain", 0),
            "asset_type": prop.get("disposal_asset_type", "residential"),
            "earned_income": _earned_income(facts),
            "spouse_earned_income": facts.get("personal", {}).get("spouse_income", 0),
        }


@adapter("strategy.sdlt_purchase_planning")
class SdltPurchasePlanningAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("property", {}).get("purchase_price", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "price": prop.get("purchase_price", 0),
            "additional_dwelling": prop.get("purchase_is_additional_dwelling", False),
            "first_time_buyer": prop.get("purchase_first_time_buyer", False),
        }


@adapter("strategy.iht_spousal_transfer_nil_rate_bands")
class IhtSpousalTransferAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("estate", {}).get("combined_estate_second_death", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        estate = facts.get("estate", {})
        return {
            "combined_estate_second_death": estate.get("combined_estate_second_death", 0),
            "combined_home_equity_second_death": estate.get(
                "combined_home_equity_second_death", 0
            ),
            "home_passes_to_direct_descendants": estate.get(
                "home_passes_to_direct_descendants", False
            ),
        }


@adapter("strategy.iht_lifetime_gifting")
class IhtLifetimeGiftingAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        estate = facts.get("estate", {})
        has_estate = (
            estate.get("combined_estate_second_death", 0) > 0
            or estate.get("gross_value", 0) > 0
        )
        return has_estate and estate.get("planned_lifetime_gift", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        estate = facts.get("estate", {})
        return {
            "planned_gift": estate.get("planned_lifetime_gift", 0),
            "prior_year_annual_exemption_unused": estate.get(
                "prior_year_annual_exemption_unused", False
            ),
            **_estate_basis(facts),
        }


@adapter("strategy.iht_charitable_legacy_reduced_rate")
class IhtCharitableLegacyAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        estate = facts.get("estate", {})
        return (
            estate.get("combined_estate_second_death", 0) > 0
            or estate.get("gross_value", 0) > 0
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        estate = facts.get("estate", {})
        return {
            "current_charitable_legacy": estate.get("charitable_legacy", 0),
            **_estate_basis(facts),
        }
