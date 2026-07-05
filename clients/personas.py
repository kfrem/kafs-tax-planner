"""Canonical test personas spanning the complexity range the product serves.

These three fact sets are used BOTH by the ``seed_demo_clients`` management
command (so the demo firm always has them) and by the automated persona
consistency tests (``advice/tests/test_personas.py``), so any engine change
is exercised against a simple, a typical, and a complex client before it can
merge. Do not change these facts casually: the tests pin hand-computed
expectations to them.

EMMA (simple)   — part-time employee, low income, married. Two strategies
                  should fire: Marriage Allowance (eligible, £252/yr) and a
                  small pension contribution.
SARAH (typical) — owner-manager with a company, a sole-trade side business,
                  pension carry-forward, and a household estate. The persona
                  used throughout the build walkthrough.
VICTOR (complex)— additional-rate taxpayer: large company, £85k sole trade,
                  £30k other income, tapered pension annual allowance, £4.5m
                  household estate with RNRB fully tapered away.
"""

EMMA_FACTS = {
    "personal": {
        "other_income": 0,
        "employment_income": 9000,  # part-time PAYE job
        "salary_from_own_company": 0,
        "dividends_from_own_company": 0,
        "spouse_income": 30000,
    },
    "company": {
        "profit_before_remuneration": 0,
        "employment_allowance_available": False,
        "associated_companies": 0,
    },
    "sole_trade": {"annual_profit": 0},
    "pension": {
        "threshold_income": 0,
        "adjusted_income": 0,
        "unused_aa_prior_3_years": [0, 0, 0],
        "desired_contribution": 2000,
    },
    "estate": {},
}

SARAH_FACTS = {
    "personal": {
        "other_income": 0,
        "salary_from_own_company": 0,
        "dividends_from_own_company": 0,
        "spouse_income": 11000,
    },
    "company": {
        "profit_before_remuneration": 95000,
        "employment_allowance_available": False,
        "associated_companies": 0,
    },
    "sole_trade": {"annual_profit": 28000},
    "pension": {
        "threshold_income": 0,
        "adjusted_income": 0,
        "unused_aa_prior_3_years": [12000, 8000, 5000],
        "desired_contribution": 40000,
    },
    "estate": {
        "gross_value": 1100000,
        "liabilities": 100000,
        "home_equity_value": 300000,
        "home_passes_to_direct_descendants": True,
        "amount_to_spouse": 1000000,
        "charitable_legacy": 0,
        "combined_estate_second_death": 1900000,
        "combined_home_equity_second_death": 600000,
        "planned_lifetime_gift": 100000,
        "prior_year_annual_exemption_unused": True,
    },
}

VICTOR_FACTS = {
    "personal": {
        "other_income": 30000,  # rental income
        "salary_from_own_company": 0,
        "dividends_from_own_company": 0,
        "spouse_income": 110000,  # additional/higher-rate spouse: no MA
    },
    "company": {
        "profit_before_remuneration": 480000,  # above marginal relief band
        "employment_allowance_available": False,
        "associated_companies": 0,
    },
    "sole_trade": {"annual_profit": 85000},
    "pension": {
        # High earner: annual allowance tapered.
        # threshold 300,000 > 200,000; adjusted 350,000 -> excess 90,000 ->
        # reduction 45,000 -> AA this year 15,000; carry-forward 90,000.
        "threshold_income": 300000,
        "adjusted_income": 350000,
        "unused_aa_prior_3_years": [40000, 30000, 20000],
        "desired_contribution": 120000,
    },
    "estate": {
        "gross_value": 3200000,
        "liabilities": 200000,
        "home_equity_value": 900000,
        "home_passes_to_direct_descendants": True,
        "amount_to_spouse": 3000000,
        "charitable_legacy": 50000,
        "combined_estate_second_death": 4500000,
        "combined_home_equity_second_death": 1200000,
        "planned_lifetime_gift": 500000,
        "prior_year_annual_exemption_unused": True,
    },
    "property": {
        # Selling a long-held rental flat (never his residence): gain
        # 150,000. Both spouses are higher-rate, so the spousal transfer
        # saves only the second annual exempt amount — the tool must say
        # so honestly rather than oversell the play.
        "disposal_gain": 150000,
        "disposal_asset_type": "residential",
        "ownership_months": 120,
        "occupied_as_main_residence_months": 0,
        "spouse_available_for_transfer": True,
        "purchase_price": 0,
    },
}

PERSONAS = [
    ("H001", "Emma Hughes", "individual", EMMA_FACTS),
    ("M042", "Sarah Mitchell", "individual_with_company", SARAH_FACTS),
    ("A007", "Victor Adeyemi", "individual_with_company", VICTOR_FACTS),
]
