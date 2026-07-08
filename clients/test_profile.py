"""The plain-English client profile reads the facts back correctly."""

from clients.personas import EMMA_FACTS, VICTOR_FACTS
from clients.profile import client_profile


def test_owner_manager_with_estate_is_described():
    p = client_profile(VICTOR_FACTS)
    assert "owner-manager" in p["headline"]
    assert "estate to plan" in p["headline"]
    titles = {s["title"] for s in p["sections"]}
    assert {"Income", "Business", "Wealth & property", "Goals & plans"} <= titles
    # money is formatted with £ and thousands separators
    all_points = " ".join(pt for s in p["sections"] for pt in s["points"])
    assert "£85,000" in all_points  # the sole-trade profit
    assert "£500,000" in all_points  # the planned lifetime gift


def test_simple_employee_profile_is_minimal():
    p = client_profile(EMMA_FACTS)
    titles = {s["title"] for s in p["sections"]}
    # Emma has employment income, a spouse and a small pension plan — no business.
    assert "Business" not in titles
    assert "Income" in titles


def test_empty_facts_do_not_crash():
    p = client_profile({})
    assert p["headline"]
    assert p["sections"] == []
