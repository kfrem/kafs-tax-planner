"""Guided intake: the engine surfaces the material questions the app would
otherwise assume, so the accountant confirms them before relying on the advice.
Pure-logic tests — no DB needed.
"""

from advice.intake import intake_gaps


def _keys(facts):
    return {g["key"] for g in intake_gaps(facts)}


def test_marital_status_is_always_asked_when_not_recorded():
    # No spouse_income key at all -> the engine flags that it assumed no spouse.
    gaps = intake_gaps({"personal": {}})
    assert "marital_status" in {g["key"] for g in gaps}
    # And recording it (even as 0) answers the question.
    assert "marital_status" not in _keys({"personal": {"spouse_income": 0}})


def test_property_jurisdiction_asked_only_for_a_transaction():
    assert "property_jurisdiction" not in _keys({"personal": {"spouse_income": 0}})
    facts = {"personal": {"spouse_income": 0}, "property": {"purchase_price": 500000}}
    assert "property_jurisdiction" in _keys(facts)
    facts["property"]["jurisdiction"] = "scotland"
    assert "property_jurisdiction" not in _keys(facts)


def test_landlord_mortgage_assumption_flagged():
    facts = {"personal": {"spouse_income": 0}, "property": {"rental_income": 24000}}
    assert "landlord_mortgage" in _keys(facts)
    facts["property"]["finance_costs"] = 0  # confirmed unmortgaged
    assert "landlord_mortgage" not in _keys(facts)


def test_bpr_qualification_and_trust_prior_transfers():
    facts = {
        "personal": {"spouse_income": 0},
        "estate": {"qualifying_business_property": 2000000},
        "trust": {"trust_value": 600000},
    }
    keys = _keys(facts)
    assert "bpr_qualification" in keys
    assert "trust_prior_transfers" in keys
    facts["estate"]["bpr_qualification_confirmed"] = True
    facts["trust"]["available_nrb"] = 325000
    keys = _keys(facts)
    assert "bpr_qualification" not in keys
    assert "trust_prior_transfers" not in keys


def test_partnership_and_pension_taper_questions():
    facts = {
        "personal": {"spouse_income": 0, "desired_pension_contribution": 20000},
        "partnership": {"total_profit": 100000},
    }
    keys = _keys(facts)
    assert "partnership_commercial" in keys
    assert "pension_taper" in keys


def test_ated_asked_when_a_portfolio_may_be_incorporated():
    facts = {"personal": {"spouse_income": 0}, "property": {"portfolio_value": 1000000}}
    assert "ated_on_incorporation" in _keys(facts)
    facts["property"]["ated_relief_confirmed"] = True
    assert "ated_on_incorporation" not in _keys(facts)


def test_a_fully_recorded_simple_client_has_no_gaps():
    # An employee whose marital status is recorded and who has no property,
    # business, pension, partnership or trust facts: nothing is assumed.
    assert intake_gaps({"personal": {"spouse_income": 30000}}) == []
