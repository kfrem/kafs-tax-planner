"""Real client scenarios engineered to exercise EVERY registered strategy
end-to-end, used by the ``self_audit`` management command (and its test).

The three canonical personas (Emma/Sarah/Victor) cover the simple/typical/
complex income-and-IHT range. This module adds:

* DANIEL — a comprehensive owner-manager whose facts trigger the Tier-1 and
  Tier-2 additions (salary sacrifice, both pension routes, group relief,
  bed-and-ISA, BPR, EIS/SEIS/VCT) plus Gift Aid, a director's loan, timing of
  disposals, capital allowances and Business Asset Disposal Relief.
* A CGT homeowner whose property was a former main residence with a let
  period (PPR, lettings relief, spousal transfer).
* Nine land-transaction cases: residential purchase, non-residential purchase
  and a lease, in each of England, Scotland and Wales, so every SDLT/LBTT/LTT
  strategy fires.

``self_audit`` asserts the UNION of strategies fired across these cases equals
the full registered set — so no strategy can ship without a real case proving
it end-to-end (advice → PDF → four-expert panel → independent recomputation).
"""

from __future__ import annotations

from clients.personas import EMMA_FACTS, SARAH_FACTS, VICTOR_FACTS

# A comprehensive owner-manager: trading company in a group, a share portfolio,
# EIS appetite, two pension routes, a director's loan, capital spend, a business
# sale (BADR) and a large business for IHT.
DANIEL_FACTS = {
    "personal": {
        "other_income": 0,
        "employment_income": 0,
        "salary_from_own_company": 70000,
        "dividends_from_own_company": 30000,
        "spouse_income": 15000,
        "gift_aid_donation": 2000,
        "divisible_capital_gain": 15000,
        "salary_sacrifice_amount": 10000,
        "desired_pension_contribution": 20000,
        "isa_amount_to_shelter": 20000,
        "isa_realised_gain": 2500,
        "isa_annual_dividend_income": 800,
        "venture_capital_investment": 50000,
        "venture_capital_scheme": "eis",
        "venture_capital_gain_reinvested": 20000,
        "income_tax_liability": 25000,
        # The four charitable/timing planning additions (July 2026): a
        # dividend he controls the timing of, a payroll-giving pledge, and a
        # gift of listed shares standing at a gain.
        "shiftable_income": 20000,
        "shiftable_income_type": "dividend",
        "payroll_giving_annual": 1200,
        "charity_asset_gift_value": 20000,
        "charity_asset_held_gain": 10000,
    },
    "company": {
        "profit_before_remuneration": 300000,
        "employment_allowance_available": False,
        "associated_companies": 1,
        "desired_employer_pension_contribution": 20000,
        "surrendering_company_loss": 50000,
        "claimant_company_profit": 250000,
        "overdrawn_loan_balance": 40000,
        "repaid_within_9_months": 10000,
        "qualifying_capital_spend": 60000,
        # Profits he does not need personally, retained via a holding company.
        "holdco_retention_amount": 100000,
    },
    "sole_trade": {"annual_profit": 0},
    "property": {
        # A separate business-asset sale qualifying for BADR.
        "badr_qualifying_gain": 500000,
        # And a trade premises sale mostly reinvested — rollover relief.
        "rollover_disposal_proceeds": 500000,
        "rollover_disposal_gain": 200000,
        "rollover_replacement_cost": 450000,
    },
    "estate": {
        "gross_value": 3000000,
        "liabilities": 0,
        "qualifying_business_property": 2000000,
        "home_equity_value": 600000,
        "home_passes_to_direct_descendants": True,
        "combined_estate_second_death": 2500000,
        "combined_home_equity_second_death": 600000,
        "charitable_legacy": 100000,
        "planned_lifetime_gift": 200000,
        "prior_year_annual_exemption_unused": True,
    },
}

# A homeowner disposing of a former main residence that was also let for a
# period: PPR relief, lettings relief and the spousal transfer before disposal.
CGT_HOMEOWNER_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {"profit_before_remuneration": 0},
    "sole_trade": {"annual_profit": 0},
    "property": {
        "disposal_gain": 120000,
        "disposal_asset_type": "residential",
        "ownership_months": 240,
        "occupied_as_main_residence_months": 120,
        # A lodger / part-let while the owner lived there — the post-2020
        # shared-occupancy test that lettings relief now requires.
        "shared_occupancy_let_fraction": 0.4,
        "spouse_available_for_transfer": True,
        "purchase_price": 0,
    },
    "estate": {},
}


# A business owner planning an exit and their estate: an EOT sale, a pension pot
# facing the April-2027 IHT change, and a life policy to fund the bill.
EXIT_AND_ESTATE_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {"profit_before_remuneration": 0, "eot_disposal_gain": 2000000},
    "sole_trade": {"annual_profit": 0},
    "estate": {
        "pension_pot_value": 500000,
        "life_policy_sum_assured": 400000,
        "estate_above_nrb": True,
    },
}


# An innovative trading company: R&D spend, patented products, and a commercial
# building with integral-feature fixtures.
INNOVATIVE_COMPANY_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {
        "profit_before_remuneration": 0,
        "qualifying_rd_spend": 100000,
        "patent_profit": 200000,
        "fixtures_value": 200000,
        "marginal_rate": 0.25,
        # A capital programme of new main-rate plant above the AIA cap.
        "full_expensing_new_plant_spend": 1500000,
    },
    "sole_trade": {"annual_profit": 0},
    "estate": {},
}


# A settlor funding a discretionary (relevant-property) trust — entry,
# ten-year and exit charges.
TRUST_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {"profit_before_remuneration": 0},
    "sole_trade": {"annual_profit": 0},
    "trust": {
        "amount_settled": 500000,
        "trust_value": 600000,
        "amount_distributed": 100000,
        "quarters_since_last_charge": 20,
    },
    "estate": {},
}


# A two-partner firm (e.g. a married couple) where one partner has other
# income — the profit-share allocation strategy.
PARTNERSHIP_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {"profit_before_remuneration": 0},
    "sole_trade": {"annual_profit": 0},
    "partnership": {
        "total_profit": 100000,
        "partner1_other_income": 40000,
        "partner2_other_income": 0,
        "current_partner1_share": 0.5,
        "proposed_partner1_share": 0.3,
    },
    "estate": {},
}


# An employee leaving with a redundancy / settlement package — the termination
# payment strategy (£30,000 exemption, excess top-sliced, employer Class 1A).
TERMINATION_FACTS = {
    "personal": {"other_income": 0, "spouse_income": 0},
    "company": {"profit_before_remuneration": 0},
    "sole_trade": {"annual_profit": 0},
    "employment": {
        "termination_payment": 50000,   # qualifying ex-gratia amount only
        "other_income": 40000,          # salary earned earlier in the year
    },
    "estate": {},
}


# A higher-rate landlord with a mortgaged residential let — the s.24
# finance-cost restriction, plus the CGT position if the let is later sold.
LANDLORD_FACTS = {
    "personal": {"other_income": 55000, "spouse_income": 0},  # salary
    "company": {"profit_before_remuneration": 0},
    "sole_trade": {"annual_profit": 0},
    "property": {
        "rental_income": 24000,
        "allowable_expenses": 4000,
        "finance_costs": 12000,
        # ...and weighing whether to incorporate the portfolio.
        "portfolio_value": 1000000,
        "latent_gain": 300000,
        "s162_relief_available": True,
        # ...the let was a furnished holiday let until the April-2025 abolition.
        "former_fhl": True,
        "capital_allowances_pool_bf": 10000,
    },
    "estate": {},
}


def _land_case(jurisdiction: str) -> dict:
    """A client making three separate land transactions in one jurisdiction:
    a residential purchase, a non-residential purchase and a lease. Each land
    case carries only one property transaction, so we emit three per region."""
    return jurisdiction


def _residential_purchase(jurisdiction: str) -> dict:
    return {
        "personal": {}, "company": {}, "sole_trade": {}, "estate": {},
        "property": {
            "purchase_price": 600000,
            "jurisdiction": jurisdiction,
            "property_type": "residential",
            "is_additional_dwelling": True,
        },
    }


def _non_residential_purchase(jurisdiction: str) -> dict:
    return {
        "personal": {}, "company": {}, "sole_trade": {}, "estate": {},
        "property": {
            "purchase_price": 800000,
            "jurisdiction": jurisdiction,
            "property_type": "non_residential",
        },
    }


def _lease(jurisdiction: str) -> dict:
    return {
        "personal": {}, "company": {}, "sole_trade": {}, "estate": {},
        "property": {
            "jurisdiction": jurisdiction,
            "property_type": "non_residential",
            "lease_annual_rent": 50000,
            "lease_term_years": 10,
            "lease_premium": 100000,
        },
    }


def _build_cases():
    cases = [
        ("AUDIT-EMMA", "Audit: Emma (simple)", "individual", EMMA_FACTS),
        ("AUDIT-SARAH", "Audit: Sarah (typical)", "individual_with_company", SARAH_FACTS),
        ("AUDIT-VICTOR", "Audit: Victor (complex)", "individual_with_company", VICTOR_FACTS),
        ("AUDIT-DANIEL", "Audit: Daniel (comprehensive owner-manager)",
         "individual_with_company", DANIEL_FACTS),
        ("AUDIT-HOME", "Audit: CGT homeowner", "individual", CGT_HOMEOWNER_FACTS),
        ("AUDIT-LANDLORD", "Audit: mortgaged landlord (s.24)", "individual", LANDLORD_FACTS),
        ("AUDIT-PARTNERSHIP", "Audit: two-partner firm", "partnership", PARTNERSHIP_FACTS),
        ("AUDIT-TRUST", "Audit: discretionary trust", "trust", TRUST_FACTS),
        ("AUDIT-INNOVCO", "Audit: innovative company (R&D/patent/fixtures)",
         "company", INNOVATIVE_COMPANY_FACTS),
        ("AUDIT-EXIT", "Audit: exit & estate (EOT/pension/life-in-trust)",
         "individual_with_company", EXIT_AND_ESTATE_FACTS),
        ("AUDIT-TERMINATION", "Audit: employment termination payment",
         "individual", TERMINATION_FACTS),
    ]
    for juris, tag in (("england", "ENG"), ("scotland", "SCO"), ("wales", "WAL")):
        cases.append((f"AUDIT-{tag}-RES", f"Audit: {juris} residential purchase",
                      "individual", _residential_purchase(juris)))
        cases.append((f"AUDIT-{tag}-NONRES", f"Audit: {juris} non-residential purchase",
                      "individual", _non_residential_purchase(juris)))
        cases.append((f"AUDIT-{tag}-LEASE", f"Audit: {juris} commercial lease",
                      "individual", _lease(juris)))
    # A shop-with-flat purchase where mixed-use classification is in point.
    cases.append(("AUDIT-ENG-MIXED", "Audit: england mixed-use purchase", "individual", {
        "personal": {}, "company": {}, "sole_trade": {}, "estate": {},
        "property": {
            "purchase_price": 800000,
            "jurisdiction": "england",
            "mixed_use_candidate": True,
            "purchase_is_additional_dwelling": True,
        },
    }))
    return cases


AUDIT_CASES = _build_cases()
