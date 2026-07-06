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
        # Whole-income view: employment income, sole-trade profit and other
        # income fill the client's bands/taper before any extraction is
        # layered on top.
        other_income = (
            personal.get("other_income", 0)
            + personal.get("employment_income", 0)
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
        employment = personal.get("employment_income", 0)
        # Relevant UK earnings (FA 2004 s.190): employment and trading income
        # only — dividends and 'other' income (which may be rent/savings) are
        # excluded from the personal-contribution relief cap.
        relevant_uk_earnings = salary + sole_trade_profit + employment
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
        other_income = (
            personal.get("other_income", 0)
            + personal.get("employment_income", 0)
            + personal.get("salary_from_own_company", 0)
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
            + personal.get("employment_income", 0)
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
        personal.get("employment_income", 0)
        + personal.get("other_income", 0)
        + personal.get("salary_from_own_company", 0)
        + facts.get("sole_trade", {}).get("annual_profit", 0)
    )


def _dividend_income(facts: dict) -> float:
    """Dividends the client actually receives — they sit below a capital gain
    in the tax bands (TCGA 1992 s.1I), so a disposal composes with them."""
    personal = facts.get("personal", {})
    return personal.get("dividends_from_own_company", 0) + personal.get("other_dividends", 0)


@adapter("strategy.directors_loan_s455")
class DirectorsLoanS455Adapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("company", {}).get("overdrawn_loan_balance", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        company = facts.get("company", {})
        return {
            "overdrawn_loan_balance": company.get("overdrawn_loan_balance", 0),
            "repaid_within_9_months": company.get("loan_repaid_within_9_months", 0),
        }


@adapter("strategy.capital_allowances")
class CapitalAllowancesAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("company", {}).get("qualifying_capital_spend", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        company = facts.get("company", {})
        result = {"qualifying_spend": company.get("qualifying_capital_spend", 0)}
        if company.get("marginal_rate"):
            result["marginal_rate"] = company["marginal_rate"]
        return result


@adapter("strategy.salary_sacrifice")
class SalarySacrificeAdapter:
    @staticmethod
    def _salary(facts: dict) -> float:
        personal = facts.get("personal", {})
        return personal.get("employment_income", 0) + personal.get(
            "salary_from_own_company", 0
        )

    @staticmethod
    def is_eligible(facts: dict) -> bool:
        personal = facts.get("personal", {})
        return (
            personal.get("salary_sacrifice_amount", 0) > 0
            and SalarySacrificeAdapter._salary(facts) > 0
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        personal = facts.get("personal", {})
        return {
            "salary": SalarySacrificeAdapter._salary(facts),
            "sacrifice_amount": personal.get("salary_sacrifice_amount", 0),
        }


@adapter("strategy.gift_aid_relief")
class GiftAidAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("personal", {}).get("gift_aid_donation", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        personal = facts.get("personal", {})
        return {
            "earned_income": _earned_income(facts),
            "dividend_income": _dividend_income(facts),
            "gross_pension_contribution": personal.get("gross_pension_contribution", 0),
            "gift_aid_donation": personal.get("gift_aid_donation", 0),
        }


@adapter("strategy.cgt_timing_of_disposals")
class CgtTimingOfDisposalsAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        # Divisible holdings only (shares/units); a single property can't be
        # part-sold across years, so this is a distinct fact from a property
        # disposal.
        return facts.get("personal", {}).get("divisible_capital_gain", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        return {
            "disposal_gain": facts.get("personal", {}).get("divisible_capital_gain", 0),
            "asset_type": "other",
            "earned_income": _earned_income(facts),
            "dividend_income": _dividend_income(facts),
        }


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
            "dividend_income": _dividend_income(facts),
        }


@adapter("strategy.cgt_lettings_relief")
class CgtLettingsReliefAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        # Post-2020 relief needs shared occupancy: an entered let-fraction of
        # the residence (a lodger / part-let while the owner lives there).
        return (
            prop.get("disposal_gain", 0) > 0
            and prop.get("shared_occupancy_let_fraction", 0) > 0
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "disposal_gain": prop.get("disposal_gain", 0),
            "let_fraction": prop.get("shared_occupancy_let_fraction", 0),
            "earned_income": _earned_income(facts),
            "dividend_income": _dividend_income(facts),
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
            "dividend_income": _dividend_income(facts),
            "spouse_earned_income": facts.get("personal", {}).get("spouse_income", 0),
            "spouse_dividend_income": facts.get("personal", {}).get("spouse_dividends", 0),
        }


@adapter("strategy.cgt_business_asset_disposal_relief")
class CgtBadrAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return facts.get("property", {}).get("badr_qualifying_gain", 0) > 0

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "disposal_gain": prop.get("badr_qualifying_gain", 0),
            "earned_income": _earned_income(facts),
            "dividend_income": _dividend_income(facts),
            "badr_lifetime_limit_used": prop.get("badr_lifetime_limit_used", 0),
        }


@adapter("strategy.sdlt_purchase_planning")
class SdltPurchasePlanningAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        # England/NI residential only; Scotland (LBTT), Wales (LTT) and
        # non-residential purchases have their own strategies. A property
        # with no jurisdiction/type recorded defaults to England residential,
        # preserving prior behaviour.
        return (
            prop.get("purchase_price", 0) > 0
            and prop.get("jurisdiction", "england") not in ("scotland", "wales")
            and prop.get("property_type", "residential") != "non_residential"
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "price": prop.get("purchase_price", 0),
            "additional_dwelling": prop.get("purchase_is_additional_dwelling", False),
            "first_time_buyer": prop.get("purchase_first_time_buyer", False),
        }


@adapter("strategy.lbtt_purchase_planning")
class LbttPurchasePlanningAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        return (
            prop.get("purchase_price", 0) > 0
            and prop.get("jurisdiction") == "scotland"
            and prop.get("property_type", "residential") != "non_residential"
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "price": prop.get("purchase_price", 0),
            "additional_dwelling": prop.get("purchase_is_additional_dwelling", False),
            "first_time_buyer": prop.get("purchase_first_time_buyer", False),
        }


@adapter("strategy.ltt_purchase_planning")
class LttPurchasePlanningAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        prop = facts.get("property", {})
        return (
            prop.get("purchase_price", 0) > 0
            and prop.get("jurisdiction") == "wales"
            and prop.get("property_type", "residential") != "non_residential"
        )

    @staticmethod
    def to_facts(facts: dict) -> dict:
        prop = facts.get("property", {})
        return {
            "price": prop.get("purchase_price", 0),
            "additional_dwelling": prop.get("purchase_is_additional_dwelling", False),
        }


def _non_residential_price(facts: dict) -> dict:
    return {"price": facts.get("property", {}).get("purchase_price", 0)}


def _non_residential_eligible(facts: dict, jurisdictions, exclude=False) -> bool:
    prop = facts.get("property", {})
    if prop.get("purchase_price", 0) <= 0 or prop.get("property_type") != "non_residential":
        return False
    juris = prop.get("jurisdiction", "england")
    return (juris not in jurisdictions) if exclude else (juris in jurisdictions)


@adapter("strategy.sdlt_non_residential_purchase")
class SdltNonResidentialAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _non_residential_eligible(facts, ("scotland", "wales"), exclude=True)

    to_facts = staticmethod(_non_residential_price)


@adapter("strategy.lbtt_non_residential_purchase")
class LbttNonResidentialAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _non_residential_eligible(facts, ("scotland",))

    to_facts = staticmethod(_non_residential_price)


@adapter("strategy.ltt_non_residential_purchase")
class LttNonResidentialAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _non_residential_eligible(facts, ("wales",))

    to_facts = staticmethod(_non_residential_price)


def _lease_facts(facts: dict) -> dict:
    prop = facts.get("property", {})
    return {
        "annual_rent": prop.get("lease_annual_rent", 0),
        "term_years": prop.get("lease_term_years", 0),
    }


def _lease_eligible(facts: dict, jurisdictions, exclude=False) -> bool:
    prop = facts.get("property", {})
    if prop.get("lease_annual_rent", 0) <= 0 or prop.get("lease_term_years", 0) <= 0:
        return False
    juris = prop.get("jurisdiction", "england")
    return (juris not in jurisdictions) if exclude else (juris in jurisdictions)


@adapter("strategy.sdlt_lease_npv")
class SdltLeaseAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _lease_eligible(facts, ("scotland", "wales"), exclude=True)

    to_facts = staticmethod(_lease_facts)


@adapter("strategy.lbtt_lease_npv")
class LbttLeaseAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _lease_eligible(facts, ("scotland",))

    to_facts = staticmethod(_lease_facts)


@adapter("strategy.ltt_lease_npv")
class LttLeaseAdapter:
    @staticmethod
    def is_eligible(facts: dict) -> bool:
        return _lease_eligible(facts, ("wales",))

    to_facts = staticmethod(_lease_facts)


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
