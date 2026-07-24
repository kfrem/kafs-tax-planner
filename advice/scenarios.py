"""Scenario modelling: 'what if the facts were different?' side-by-side
comparisons for the reviewing accountant. Deliberately EPHEMERAL — a
scenario is decision-support scratch work, computed through exactly the
same engine path as real advice but never stored, so the audit trail
contains only advice the professional actually generated.
"""

from __future__ import annotations

import copy

from .generator import compute_strategy_results

# Headline metric per strategy, for the comparison table. Full
# quantifications are shown alongside; this is the at-a-glance number.
HEADLINES = {
    "salary-dividend-mix": ("Net to individual", lambda q: q.get("recommended", {}).get("net_to_individual")),
    "incorporation-vs-sole-trade": ("Incorporated total tax/NIC", lambda q: (q.get("incorporated") or {}).get("total_tax_and_nic")),
    "pension-annual-allowance-carry-forward": ("Personal relief value", lambda q: q.get("personal_route", {}).get("total_relief_value")),
    "marriage-allowance-transfer": ("Annual saving", lambda q: q.get("estimated_annual_tax_saving")),
    "iht-spousal-transfer-and-nil-rate-bands": ("Second-death tax", lambda q: q.get("second_death_with_transferred_bands", {}).get("tax_due")),
    "iht-lifetime-gifting-pets": ("Saving if survive 7 years", lambda q: q.get("saving_if_survive_7_years")),
    "iht-charitable-legacy-reduced-rate": ("Net cost to beneficiaries", lambda q: q.get("net_cost_to_beneficiaries")),
    "cgt-ppr-relief": ("CGT after relief", lambda q: q.get("cgt_with_relief")),
    "cgt-spousal-transfer-before-disposal": ("Saving from transfer", lambda q: q.get("saving")),
    "sdlt-purchase-planning": ("Total SDLT", lambda q: (q.get("as_planned") or {}).get("total_sdlt")),
    "income-timing-across-years": ("Saving from timing", lambda q: q.get("saving")),
    "payroll-giving": ("Income tax saved", lambda q: q.get("income_tax_saved")),
    "charity-gift-of-assets": ("Total tax benefit", lambda q: q.get("total_tax_benefit")),
    "cgt-rollover-relief": ("Tax deferred", lambda q: q.get("tax_deferred")),
    "capital-allowances-full-expensing": ("Tax saved year one", lambda q: q.get("tax_saved_year_one")),
    "holding-company-structuring": ("Tax deferred", lambda q: q.get("tax_deferred_by_retention")),
    "sdlt-mixed-use-classification": ("Saving if mixed-use", lambda q: q.get("saving_if_mixed_use")),
}


def apply_overrides(facts: dict, overrides: dict) -> dict:
    """Deep-copies the facts and sets dot-path overrides, e.g.
    {"pension.desired_contribution": 10000}."""
    modified = copy.deepcopy(facts)
    for path, value in overrides.items():
        node = modified
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return modified


def run_scenario(facts: dict, tax_year: str, overrides: dict) -> dict:
    base_results = compute_strategy_results(facts, tax_year)
    scenario_results = compute_strategy_results(apply_overrides(facts, overrides), tax_year)

    base_by_code = {r["strategy_code"]: r for r in base_results}
    scenario_by_code = {r["strategy_code"]: r for r in scenario_results}

    comparison = []
    for code in sorted(set(base_by_code) | set(scenario_by_code)):
        label, extract = HEADLINES.get(code, ("—", lambda q: None))
        base = base_by_code.get(code)
        scenario = scenario_by_code.get(code)
        base_value = extract(base["quantification"]) if base else None
        scenario_value = extract(scenario["quantification"]) if scenario else None
        delta = (
            round(scenario_value - base_value, 2)
            if isinstance(base_value, (int, float)) and isinstance(scenario_value, (int, float))
            else None
        )
        comparison.append(
            {
                "code": code,
                "name": (scenario or base)["strategy_name"],
                "headline": label,
                "base": base_value,
                "scenario": scenario_value,
                "delta": delta,
                "only_in": (
                    "scenario" if base is None else "base" if scenario is None else None
                ),
            }
        )

    return {
        "overrides": overrides,
        "base_results": base_results,
        "scenario_results": scenario_results,
        "comparison": comparison,
    }
