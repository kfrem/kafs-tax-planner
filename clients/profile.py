"""Turn a client's recorded facts into a plain-English 'who is this person'
profile — the picture an adviser forms before working out the tax. Deterministic
and read-only: it simply reads the facts back in words, grouped by dimension, so
the accountant (and the client) can sanity-check that the software has understood
the situation before relying on the advice.
"""

from __future__ import annotations


def _money(v):
    try:
        return f"£{float(v):,.0f}"
    except (TypeError, ValueError):
        return str(v)


def client_profile(facts: dict) -> dict:
    """Return {headline, sections:[{title, points:[str]}]} describing the client."""
    p = facts.get("personal", {}) or {}
    company = facts.get("company", {}) or {}
    sole = facts.get("sole_trade", {}) or {}
    pension = facts.get("pension", {}) or {}
    estate = facts.get("estate", {}) or {}
    prop = facts.get("property", {}) or {}

    income, family, business, wealth, plans = [], [], [], [], []

    # Income
    if p.get("employment_income"):
        income.append(f"Employed, earning {_money(p['employment_income'])} a year.")
    if p.get("salary_from_own_company"):
        income.append(f"Takes a salary of {_money(p['salary_from_own_company'])} from their own company.")
    if p.get("dividends_from_own_company"):
        income.append(f"Takes {_money(p['dividends_from_own_company'])} of dividends from their own company.")
    if sole.get("annual_profit"):
        income.append(f"Runs a self-employed business making {_money(sole['annual_profit'])} profit.")
    if p.get("other_income"):
        income.append(f"Has {_money(p['other_income'])} of other income (e.g. rent or savings).")

    # Family
    if p.get("spouse_income") is not None and (p.get("spouse_income") or "spouse_income" in p):
        if p.get("spouse_income"):
            family.append(f"Married or in a civil partnership; the spouse earns {_money(p['spouse_income'])}.")
        else:
            family.append("Married or in a civil partnership (spouse has no recorded income).")
    if estate.get("home_passes_to_direct_descendants"):
        family.append("Intends the family home to pass to children or grandchildren.")

    # Business
    if company.get("profit_before_remuneration"):
        line = f"Owns a company making {_money(company['profit_before_remuneration'])} profit before their pay."
        if company.get("associated_companies"):
            line += f" It has {company['associated_companies']} associated company(ies)."
        business.append(line)

    # Wealth / estate
    if estate.get("combined_estate_second_death"):
        wealth.append(f"Combined household estate of about {_money(estate['combined_estate_second_death'])} (second death).")
    elif estate.get("gross_value"):
        net = float(estate.get("gross_value", 0)) - float(estate.get("liabilities", 0) or 0)
        wealth.append(f"Estate of about {_money(net)} after liabilities.")
    if prop.get("disposal_gain"):
        wealth.append(f"Sitting on a {_money(prop['disposal_gain'])} gain from a property they may sell.")
    if prop.get("purchase_price"):
        wealth.append(f"Considering a property purchase of {_money(prop['purchase_price'])}.")

    # Plans / goals
    if pension.get("desired_contribution"):
        plans.append(f"Wants to put {_money(pension['desired_contribution'])} into a pension this year.")
    if estate.get("planned_lifetime_gift"):
        plans.append(f"Considering a lifetime gift of {_money(estate['planned_lifetime_gift'])}.")
    if estate.get("charitable_legacy"):
        plans.append(f"Plans a charitable legacy of {_money(estate['charitable_legacy'])}.")

    # Headline
    bits = []
    if company.get("profit_before_remuneration"):
        bits.append("an owner-manager")
    if sole.get("annual_profit"):
        bits.append("a sole trader")
    if p.get("employment_income") and not bits:
        bits.append("an employee")
    if estate.get("combined_estate_second_death") or estate.get("gross_value"):
        bits.append("with an estate to plan")
    headline = "This client is " + (", ".join(bits) if bits else "an individual") + "."

    sections = [
        {"title": "Income", "points": income},
        {"title": "Family", "points": family},
        {"title": "Business", "points": business},
        {"title": "Wealth & property", "points": wealth},
        {"title": "Goals & plans", "points": plans},
    ]
    sections = [s for s in sections if s["points"]]
    return {"headline": headline, "sections": sections}
