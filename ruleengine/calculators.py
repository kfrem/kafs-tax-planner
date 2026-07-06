"""Layer 2 (pure computation) and Layer 3 (strategy quantification)
calculators, per architecture doc Section 5.2/5.3.

Layer 2 calculators are single-purpose and reusable (income tax, dividend
tax, NIC, corporation tax). Layer 3 "strategy" calculators compose Layer 2
functions to quantify a planning strategy end to end; a Strategy row's
``calculator_key`` points at one of these.

Simplifications made explicitly for MVP scope (must be reviewed by the tax
editor before any client-facing use — see Section 5.6 governance):
 - Class 2 NIC is voluntary since April 2024 and is not modelled as a cost.
 - Scottish and Welsh divergent income tax rates are out of scope (English/
   Welsh employment income tax law only, per architecture doc Section 12).
 - Marginal relief assumes augmented profits equal net profits (no franked
   investment income from other companies) — the common case for a single
   owner-managed trading company.
"""

from __future__ import annotations

import datetime

from .engine import _apply_band_rates, get_parameter, parameter_cache, register


def _apply_band_rates_with_offset(amount: float, bands: list[dict], offset: float) -> float:
    """Tax ``amount`` through ``bands`` where ``offset`` of band capacity has
    already been consumed by other income stacked underneath it."""
    tax = 0.0
    remaining = amount
    lower = 0.0
    for band in bands:
        upper = band["upper"]
        band_capacity = (upper - lower) if upper is not None else float("inf")
        available_in_band = max(0.0, band_capacity - max(0.0, offset - lower))
        amount_in_band = max(0.0, min(remaining, available_in_band))
        tax += amount_in_band * band["rate"]
        remaining -= amount_in_band
        lower = upper if upper is not None else lower
        if remaining <= 0:
            break
    return round(tax, 2)


@register(
    "income_tax_on_earned_income",
    consumes=["income_tax.personal_allowance", "income_tax.bands"],
    description="Income tax on non-dividend, non-savings income after the tapered personal allowance.",
)
def income_tax_on_earned_income(facts: dict, tax_year: str) -> dict:
    total_income = float(facts["total_income"])
    pa_param = get_parameter("income_tax.personal_allowance", tax_year)
    bands_param = get_parameter("income_tax.bands", tax_year)

    excess = max(0.0, total_income - pa_param["taper_threshold"])
    reduction = min(pa_param["amount"], excess * pa_param["taper_rate"])
    personal_allowance = round(pa_param["amount"] - reduction, 2)

    taxable_income = max(0.0, round(total_income - personal_allowance, 2))
    tax_due, breakdown = _apply_band_rates(taxable_income, bands_param["bands"])

    return {
        "total_income": total_income,
        "personal_allowance": personal_allowance,
        "taxable_income": taxable_income,
        "tax_breakdown": breakdown,
        "tax_due": tax_due,
    }


@register(
    "dividend_tax",
    consumes=["dividend_tax.allowance", "dividend_tax.bands"],
    description="Tax on dividend income, stacked on top of other taxable income, net of the dividend allowance.",
)
def dividend_tax(facts: dict, tax_year: str) -> dict:
    other_taxable_income = float(facts["other_taxable_income"])
    dividend_income = float(facts["dividend_income"])
    allowance_param = get_parameter("dividend_tax.allowance", tax_year)
    bands_param = get_parameter("dividend_tax.bands", tax_year)

    allowance = allowance_param["amount"]
    tax_without_allowance = _apply_band_rates_with_offset(
        dividend_income, bands_param["bands"], other_taxable_income
    )
    allowance_used = min(allowance, dividend_income)
    tax_relieved_by_allowance = _apply_band_rates_with_offset(
        allowance_used, bands_param["bands"], other_taxable_income
    )
    tax_due = round(tax_without_allowance - tax_relieved_by_allowance, 2)

    return {
        "dividend_income": dividend_income,
        "dividend_allowance": allowance,
        "tax_due": tax_due,
    }


@register(
    "combined_personal_tax",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Income tax and dividend tax computed together on a whole-person basis: "
    "personal allowance tapered on total income (including dividends), unused personal "
    "allowance applied to dividends, dividends stacked above earned income in the bands.",
)
def combined_personal_tax(facts: dict, tax_year: str) -> dict:
    """Whole-person personal tax. Unlike the single-purpose calculators above,
    this models the interactions between income types that materially change
    the answer for owner-managers:

     - the personal allowance taper (ITA 2007 s.35(2)) operates on adjusted
       net income INCLUDING dividends, so a large dividend can strip the
       allowance from salary;
     - personal allowance not used by earned income shelters dividends;
     - dividends occupy the tax bands above earned income.

    Documented simplifications (standard allocation order; no beneficial-
    ordering optimisation; dividend allowance modelled as relief at the
    lowest dividend slice rather than as band-consuming nil-rate) — for the
    tax editor to review per Section 5.6 governance.
    """
    earned = max(0.0, float(facts.get("earned_income", 0)))
    dividends = max(0.0, float(facts.get("dividend_income", 0)))
    # Gross relief-at-source pension contributions AND gross Gift Aid
    # donations both extend the band limits and reduce adjusted net income
    # for the taper (FA 2004 s.192 and ITA 2007 s.414 respectively; ITA 2007
    # s.35(2) via the s.58 definition of adjusted net income). They are
    # additive and mechanically identical for the band/taper calculation.
    gross_ras = max(0.0, float(facts.get("gross_pension_contribution", 0)))
    gross_gift_aid = max(0.0, float(facts.get("gross_gift_aid", 0)))
    band_extension = gross_ras + gross_gift_aid

    pa_param = get_parameter("income_tax.personal_allowance", tax_year)
    bands_param = get_parameter("income_tax.bands", tax_year)
    allowance_param = get_parameter("dividend_tax.allowance", tax_year)
    div_bands_param = get_parameter("dividend_tax.bands", tax_year)

    def _extend(bands: list[dict]) -> list[dict]:
        if not band_extension:
            return bands
        return [
            {"upper": (b["upper"] + band_extension) if b["upper"] is not None else None, "rate": b["rate"]}
            for b in bands
        ]

    total_income = earned + dividends
    adjusted_net_income = max(0.0, total_income - band_extension)
    excess = max(0.0, adjusted_net_income - pa_param["taper_threshold"])
    reduction = min(pa_param["amount"], excess * pa_param["taper_rate"])
    personal_allowance = round(pa_param["amount"] - reduction, 2)

    taxable_earned = max(0.0, round(earned - personal_allowance, 2))
    pa_remaining = max(0.0, round(personal_allowance - earned, 2))
    taxable_dividends = max(0.0, round(dividends - pa_remaining, 2))

    income_bands = _extend(bands_param["bands"])
    dividend_bands = _extend(div_bands_param["bands"])

    earned_tax, _ = _apply_band_rates(taxable_earned, income_bands)

    gross_dividend_tax = _apply_band_rates_with_offset(
        taxable_dividends, dividend_bands, taxable_earned
    )
    allowance_used = min(allowance_param["amount"], taxable_dividends)
    allowance_relief = _apply_band_rates_with_offset(
        allowance_used, dividend_bands, taxable_earned
    )
    dividend_tax_due = round(gross_dividend_tax - allowance_relief, 2)

    return {
        "earned_income": earned,
        "dividend_income": dividends,
        "gross_pension_contribution": gross_ras,
        "gross_gift_aid": gross_gift_aid,
        "adjusted_net_income": round(adjusted_net_income, 2),
        "personal_allowance": personal_allowance,
        "taxable_earned": taxable_earned,
        "taxable_dividends": taxable_dividends,
        # Total income occupying the tax bands below any capital gain — the
        # figure CGT stacks on top of (TCGA 1992 s.1I: gains are the top slice).
        "taxable_income_total": round(taxable_earned + taxable_dividends, 2),
        "earned_tax": earned_tax,
        "dividend_tax_due": dividend_tax_due,
        "total_tax": round(earned_tax + dividend_tax_due, 2),
    }


@register(
    "strategy.gift_aid_relief",
    consumes=[
        "income_tax.bands",
        "income_tax.personal_allowance",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Gift Aid relief (ITA 2007 s.414): the donation is grossed up at the basic "
    "rate, which extends the basic-rate band — giving higher/additional-rate donors relief "
    "beyond the 20% the charity reclaims — and reduces adjusted net income, which can "
    "restore the personal allowance lost in the 100,000-125,140 taper.",
)
def strategy_gift_aid_relief(facts: dict, tax_year: str) -> dict:
    earned = max(0.0, float(facts.get("earned_income", 0)))
    dividends = max(0.0, float(facts.get("dividend_income", 0)))
    existing_pension = max(0.0, float(facts.get("gross_pension_contribution", 0)))
    net = max(0.0, float(facts.get("gift_aid_donation", 0)))

    # Gross up at the basic rate: the charity reclaims that slice, and the
    # donor's basic-rate limit is extended by the gross amount.
    basic_rate = get_parameter("income_tax.bands", tax_year)["bands"][0]["rate"]
    gross = round(net / (1 - basic_rate), 2)

    base = {
        "earned_income": earned,
        "dividend_income": dividends,
        "gross_pension_contribution": existing_pension,
    }
    baseline = combined_personal_tax(base, tax_year)
    with_gift = combined_personal_tax({**base, "gross_gift_aid": gross}, tax_year)

    personal_relief = round(baseline["total_tax"] - with_gift["total_tax"], 2)
    pa_restored = round(with_gift["personal_allowance"] - baseline["personal_allowance"], 2)
    charity_reclaims = round(gross - net, 2)

    return {
        "net_donation": round(net, 2),
        "gross_donation": gross,
        "charity_reclaims": charity_reclaims,
        "personal_higher_rate_relief": personal_relief,
        "personal_allowance_restored": pa_restored,
        "total_tax_benefit": round(charity_reclaims + personal_relief, 2),
    }


@register(
    "employee_class1_nic",
    consumes=["national_insurance.employee_class1"],
    description="Employee Class 1 NIC on annual salary.",
)
def employee_class1_nic(facts: dict, tax_year: str) -> dict:
    salary = float(facts["annual_salary"])
    param = get_parameter("national_insurance.employee_class1", tax_year)
    pt, uel, rate, upper_rate = (
        param["primary_threshold"],
        param["upper_earnings_limit"],
        param["rate"],
        param["upper_rate"],
    )
    main_band = max(0.0, min(salary, uel) - pt)
    upper_band = max(0.0, salary - uel)
    nic = round(main_band * rate + upper_band * upper_rate, 2)
    return {"annual_salary": salary, "nic_due": nic}


@register(
    "employer_class1_nic",
    consumes=["national_insurance.employer_class1", "national_insurance.employment_allowance"],
    description="Employer (secondary) Class 1 NIC on annual salary, with optional Employment Allowance.",
)
def employer_class1_nic(facts: dict, tax_year: str) -> dict:
    salary = float(facts["annual_salary"])
    employment_allowance_available = bool(facts.get("employment_allowance_available", False))
    param = get_parameter("national_insurance.employer_class1", tax_year)
    st, rate = param["secondary_threshold"], param["rate"]
    gross_nic = round(max(0.0, salary - st) * rate, 2)

    relief = 0.0
    if employment_allowance_available:
        ea_param = get_parameter("national_insurance.employment_allowance", tax_year)
        relief = min(gross_nic, ea_param["amount"])
    nic_due = round(gross_nic - relief, 2)
    return {"annual_salary": salary, "gross_nic": gross_nic, "employment_allowance_relief": relief, "nic_due": nic_due}


@register(
    "corporation_tax",
    consumes=["corporation_tax.rates"],
    description="Corporation tax with marginal relief between the small profits and main rate limits.",
)
def corporation_tax(facts: dict, tax_year: str) -> dict:
    profit = max(0.0, float(facts["taxable_profit"]))
    associated_companies = int(facts.get("associated_companies", 0))
    param = get_parameter("corporation_tax.rates", tax_year)

    divisor = 1 + associated_companies
    lower_limit = param["small_profits_limit"] / divisor
    upper_limit = param["main_rate_limit"] / divisor

    if profit <= lower_limit:
        tax = profit * param["small_profits_rate"]
        marginal_relief = 0.0
        effective_rate = param["small_profits_rate"]
    elif profit >= upper_limit:
        tax = profit * param["main_rate"]
        marginal_relief = 0.0
        effective_rate = param["main_rate"]
    else:
        marginal_relief = (upper_limit - profit) * param["marginal_relief_fraction"]
        tax = profit * param["main_rate"] - marginal_relief
        effective_rate = tax / profit if profit else 0.0

    return {
        "taxable_profit": profit,
        "tax_due": round(tax, 2),
        "marginal_relief": round(marginal_relief, 2),
        "effective_rate": round(effective_rate, 4),
    }


@register(
    "pension_available_annual_allowance",
    consumes=["pension.annual_allowance"],
    description="Available pension annual allowance for a tax year including up to 3 years' carry-forward, with tapering for high earners.",
)
def pension_available_annual_allowance(facts: dict, tax_year: str) -> dict:
    threshold_income = float(facts.get("threshold_income", 0))
    adjusted_income = float(facts.get("adjusted_income", 0))
    unused_prior_years = [float(x) for x in facts.get("unused_aa_prior_3_years", [])]
    param = get_parameter("pension.annual_allowance", tax_year)

    standard_aa = param["standard_amount"]
    tapered = False
    aa_this_year = standard_aa
    if threshold_income > param["taper_threshold_income"]:
        excess = adjusted_income - param["taper_adjusted_income_limit"]
        if excess > 0:
            tapered = True
            reduction = min(standard_aa - param["minimum_tapered_amount"], excess * 0.5)
            aa_this_year = round(standard_aa - reduction, 2)

    carry_forward = sum(unused_prior_years)
    total_available = round(aa_this_year + carry_forward, 2)

    return {
        "annual_allowance_this_year": aa_this_year,
        "tapered": tapered,
        "carry_forward_available": round(carry_forward, 2),
        "total_available": total_available,
    }


# --- Layer 3: strategy quantification -------------------------------------


@register(
    "strategy.salary_dividend_mix",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "national_insurance.employee_class1",
        "national_insurance.employer_class1",
        "national_insurance.employment_allowance",
        "corporation_tax.rates",
    ],
    description="Compares salary/dividend extraction splits from an owner-managed company for a given profit before remuneration.",
)
def strategy_salary_dividend_mix(facts: dict, tax_year: str) -> dict:
    """Whole-income comparison: personal tax on each extraction option is the
    INCREMENTAL tax it causes on top of the client's other income (treated as
    non-dividend income), so sole-trade profits or employment income that
    fill the basic-rate band or trigger the personal allowance taper are
    reflected in the numbers, not ignored.

    If ``salary_options`` is supplied, only those levels are compared.
    Otherwise the optimal salary is found numerically: coarse scan then
    refinement to £1 granularity. The net function is piecewise linear in
    salary, but its breakpoints depend on interactions (NIC thresholds, CT
    marginal relief limits, band crossings of the dividend stack, the PA
    taper), so a scan is more robust than enumerating breakpoints
    analytically.
    """
    profit_before_remuneration = float(facts["company_profit_before_remuneration"])
    other_personal_income = float(facts.get("other_personal_income", 0))
    employment_allowance_available = bool(facts.get("employment_allowance_available", False))

    with parameter_cache():
        baseline = combined_personal_tax(
            {"earned_income": other_personal_income, "dividend_income": 0}, tax_year
        )

        def evaluate(salary: float) -> dict | None:
            employer_nic = employer_class1_nic(
                {"annual_salary": salary, "employment_allowance_available": employment_allowance_available},
                tax_year,
            )
            # Infeasible: the company cannot pay salary plus the employer
            # NIC on it out of the available profit.
            if salary + employer_nic["nic_due"] > profit_before_remuneration:
                return None
            taxable_profit = max(0.0, profit_before_remuneration - salary - employer_nic["nic_due"])
            ct = corporation_tax({"taxable_profit": taxable_profit}, tax_year)
            dividends_available = round(taxable_profit - ct["tax_due"], 2)

            with_extraction = combined_personal_tax(
                {
                    "earned_income": other_personal_income + salary,
                    "dividend_income": dividends_available,
                },
                tax_year,
            )
            personal_tax_on_extraction = round(
                with_extraction["total_tax"] - baseline["total_tax"], 2
            )
            employee_nic = employee_class1_nic({"annual_salary": salary}, tax_year)

            total_tax_and_nic = round(
                employer_nic["nic_due"]
                + ct["tax_due"]
                + personal_tax_on_extraction
                + employee_nic["nic_due"],
                2,
            )
            net_to_individual = round(
                salary + dividends_available - employee_nic["nic_due"] - personal_tax_on_extraction,
                2,
            )
            return {
                "salary": salary,
                "employer_nic": employer_nic["nic_due"],
                "corporation_tax": ct["tax_due"],
                "dividends_available": dividends_available,
                "personal_tax_on_extraction": personal_tax_on_extraction,
                "employee_nic": employee_nic["nic_due"],
                "total_tax_and_nic": total_tax_and_nic,
                "net_to_individual": net_to_individual,
            }

        if "salary_options" in facts:
            options = sorted(set(facts["salary_options"]))
            comparisons = [
                result
                for s in options
                if s <= profit_before_remuneration and (result := evaluate(s)) is not None
            ]
            best = max(comparisons, key=lambda c: c["net_to_individual"]) if comparisons else None
            optimised = False
        else:
            employer_param = get_parameter("national_insurance.employer_class1", tax_year)
            employee_param = get_parameter("national_insurance.employee_class1", tax_year)
            reference_salaries = sorted(
                {
                    0,
                    employer_param["secondary_threshold"],
                    employee_param["primary_threshold"],
                    employee_param["upper_earnings_limit"],
                }
            )
            optimal_salary = _scan_optimal_salary(
                evaluate, cap=min(profit_before_remuneration, 130000.0)
            )
            best = evaluate(optimal_salary)
            comparisons = [
                result
                for s in reference_salaries
                if s <= profit_before_remuneration and (result := evaluate(s)) is not None
            ]
            if optimal_salary not in [c["salary"] for c in comparisons]:
                comparisons.append(best)
                comparisons.sort(key=lambda c: c["salary"])
            optimised = True

    return {
        "profit_before_remuneration": profit_before_remuneration,
        "other_personal_income_considered": other_personal_income,
        "salary_optimised_to_nearest_pound": optimised,
        "comparisons": comparisons,
        "recommended": best,
    }


def _scan_optimal_salary(evaluate, cap: float) -> int:
    """Coarse-to-fine scan for the salary maximising net_to_individual.
    Ties resolve to the lower salary."""
    cap = int(cap)

    def best_in(start: int, stop: int, step: int, seed_salary: int, seed_net: float):
        best_salary, best_net = seed_salary, seed_net
        for s in range(start, stop + 1, step):
            result = evaluate(s)
            if result is None:
                continue
            net = result["net_to_individual"]
            if net > best_net:
                best_salary, best_net = s, net
        return best_salary, best_net

    salary, net = 0, evaluate(0)["net_to_individual"]
    salary, net = best_in(0, cap, 250, salary, net)
    salary, net = best_in(max(0, salary - 250), min(cap, salary + 250), 10, salary, net)
    salary, net = best_in(max(0, salary - 10), min(cap, salary + 10), 1, salary, net)
    return salary


@register(
    "strategy.pension_annual_allowance_carry_forward",
    consumes=[
        "pension.annual_allowance",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "corporation_tax.rates",
    ],
    description="Pension contribution planning: annual allowance with carry-forward, the "
    "relevant-UK-earnings cap on personal contribution relief (FA 2004 s.190), correct "
    "relief-at-source mechanics, and the employer-contribution alternative with its "
    "corporation tax saving.",
)
def strategy_pension_carry_forward(facts: dict, tax_year: str) -> dict:
    """Two routes are quantified:

    Personal (relief at source): tax relief only up to the greater of £3,600
    and relevant UK earnings — dividends do NOT count (FA 2004 s.190).
    Relief value = the basic-rate credit HMRC adds to the pension (gross x
    basic rate) plus the personal tax saved through band extension and any
    personal-allowance taper restoration.

    Employer: the company contributes instead — no earnings cap, no NIC, and
    a corporation tax deduction (CTA 2009 s.54 wholly-and-exclusively
    condition applies; part of the overall remuneration package question the
    reviewing accountant owns). The annual allowance still applies to the
    total pension input under either route.
    """
    desired_contribution = float(facts["desired_contribution"])
    earned_income = float(facts.get("earned_income", facts.get("total_income", 0)))
    dividend_income = float(facts.get("dividend_income", 0))
    relevant_uk_earnings = float(facts.get("relevant_uk_earnings", earned_income))
    company_profit = float(facts.get("company_profit_before_remuneration", 0))

    availability = pension_available_annual_allowance(facts, tax_year)
    aa_excess = max(0.0, desired_contribution - availability["total_available"])

    # --- Personal route ---
    relievable_gross = min(desired_contribution, max(3600.0, relevant_uk_earnings))
    unrelieved_amount = round(desired_contribution - relievable_gross, 2)

    bands_param = get_parameter("income_tax.bands", tax_year)
    basic_rate = bands_param["bands"][0]["rate"]

    without = combined_personal_tax(
        {"earned_income": earned_income, "dividend_income": dividend_income}, tax_year
    )
    with_contribution = combined_personal_tax(
        {
            "earned_income": earned_income,
            "dividend_income": dividend_income,
            "gross_pension_contribution": relievable_gross,
        },
        tax_year,
    )
    basic_rate_credit = round(relievable_gross * basic_rate, 2)
    band_extension_saving = round(without["total_tax"] - with_contribution["total_tax"], 2)

    personal_route = {
        "relievable_gross": round(relievable_gross, 2),
        "unrelieved_amount": unrelieved_amount,
        "basic_rate_credit_to_pension": basic_rate_credit,
        "personal_tax_saving": band_extension_saving,
        "total_relief_value": round(basic_rate_credit + band_extension_saving, 2),
    }

    # --- Employer route ---
    employer_route = None
    if company_profit > 0:
        contribution = min(desired_contribution, company_profit)
        ct_before = corporation_tax({"taxable_profit": company_profit}, tax_year)
        ct_after = corporation_tax(
            {"taxable_profit": company_profit - contribution}, tax_year
        )
        employer_route = {
            "contribution": round(contribution, 2),
            "corporation_tax_saving": round(ct_before["tax_due"] - ct_after["tax_due"], 2),
            "no_relevant_earnings_cap": True,
        }

    return {
        "desired_contribution": desired_contribution,
        "relevant_uk_earnings": round(relevant_uk_earnings, 2),
        "available_annual_allowance": availability["total_available"],
        "fits_within_allowance": aa_excess == 0.0,
        "amount_subject_to_annual_allowance_charge": round(aa_excess, 2),
        "personal_route": personal_route,
        "employer_route": employer_route,
    }


@register(
    "strategy.incorporation_vs_sole_trade",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "national_insurance.employee_class1",
        "national_insurance.employer_class1",
        "national_insurance.employment_allowance",
        "national_insurance.class4",
        "corporation_tax.rates",
    ],
    description="Compares sole trader income tax + Class 4 NIC against incorporating and extracting via salary/dividend.",
)
def strategy_incorporation_vs_sole_trade(facts: dict, tax_year: str) -> dict:
    annual_profit = float(facts["annual_profit"])
    other_personal_income = float(facts.get("other_personal_income", 0))

    # Incremental income tax the sole-trade profit causes on top of the
    # client's other income, so both arms of the comparison exclude tax the
    # client would pay anyway.
    baseline = combined_personal_tax(
        {"earned_income": other_personal_income, "dividend_income": 0}, tax_year
    )
    with_profit = combined_personal_tax(
        {"earned_income": other_personal_income + annual_profit, "dividend_income": 0}, tax_year
    )
    sole_trader_income_tax = round(with_profit["total_tax"] - baseline["total_tax"], 2)

    class4_param = get_parameter("national_insurance.class4", tax_year)
    lpl, upl, rate, upper_rate = (
        class4_param["lower_profits_limit"],
        class4_param["upper_profits_limit"],
        class4_param["rate"],
        class4_param["upper_rate"],
    )
    class4_nic = round(
        max(0.0, min(annual_profit, upl) - lpl) * rate + max(0.0, annual_profit - upl) * upper_rate, 2
    )
    sole_trader_total = round(sole_trader_income_tax + class4_nic, 2)

    mix_facts = {
        "company_profit_before_remuneration": annual_profit,
        "other_personal_income": other_personal_income,
    }
    if "salary_options" in facts:
        mix_facts["salary_options"] = facts["salary_options"]
    incorporated = strategy_salary_dividend_mix(mix_facts, tax_year)
    best_incorporated = incorporated["recommended"]

    return {
        "annual_profit": annual_profit,
        "other_personal_income_considered": other_personal_income,
        "sole_trader": {
            "income_tax": sole_trader_income_tax,
            "class4_nic": class4_nic,
            "total_tax_and_nic": sole_trader_total,
        },
        "incorporated": best_incorporated,
        "recommendation": "incorporate"
        if best_incorporated and best_incorporated["total_tax_and_nic"] < sole_trader_total
        else "remain_sole_trader",
    }


@register(
    "strategy.marriage_allowance_transfer",
    consumes=["income_tax.personal_allowance", "income_tax.marriage_allowance"],
    description="Marriage Allowance: transferring 10% of an unused personal allowance to a basic-rate-taxpayer spouse/civil partner.",
)
def strategy_marriage_allowance_transfer(facts: dict, tax_year: str) -> dict:
    transferor_income = float(facts["transferor_income"])
    transferee_income = float(facts["transferee_income"])

    pa_param = get_parameter("income_tax.personal_allowance", tax_year)
    bands_param = get_parameter("income_tax.bands", tax_year)
    ma_param = get_parameter("income_tax.marriage_allowance", tax_year)

    basic_rate_upper = bands_param["bands"][0]["upper"]
    transferee_taxable = max(0.0, transferee_income - pa_param["amount"])

    eligible = (
        transferor_income <= pa_param["amount"]
        and transferee_income <= pa_param["amount"] + basic_rate_upper
        and transferee_taxable > 0
    )
    transferable_amount = ma_param["transferable_amount"]
    tax_saving = round(transferable_amount * bands_param["bands"][0]["rate"], 2) if eligible else 0.0

    return {
        "eligible": eligible,
        "transferable_amount": transferable_amount,
        "estimated_annual_tax_saving": tax_saving,
    }


# --- Capital gains tax and SDLT ------------------------------------------------


@register(
    "cgt_liability",
    consumes=[
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="CGT on a chargeable gain: annual exempt amount, then the lower rate "
    "within the individual's unused basic-rate band and the higher rate above it "
    "(TCGA 1992 ss.1H-1K). The gain is the top slice: earned income AND dividends "
    "below it consume the basic-rate band, and a gross pension contribution extends "
    "it. An optional disposal_date resolves rates that change mid-year (30 Oct 2024).",
)
def cgt_liability(facts: dict, tax_year: str) -> dict:
    gain = max(0.0, float(facts.get("chargeable_gain", 0)))
    asset_type = facts.get("asset_type", "residential")
    earned_income = max(0.0, float(facts.get("earned_income", 0)))
    dividend_income = max(0.0, float(facts.get("dividend_income", 0)))
    gross_pension = max(0.0, float(facts.get("gross_pension_contribution", 0)))

    # The disposal date, when supplied, resolves intra-year rate changes
    # (30 Oct 2024). The AEA and rates are read as of that date; income tax
    # bands do not change mid-year, so they use the tax-year anchor.
    disposal_date = facts.get("disposal_date")
    as_of = datetime.date.fromisoformat(disposal_date) if disposal_date else None

    aea_param = get_parameter("cgt.annual_exempt_amount", tax_year, as_of=as_of)
    rates_param = get_parameter("cgt.rates", tax_year, as_of=as_of)
    bands_param = get_parameter("income_tax.bands", tax_year)
    rates = rates_param[asset_type]

    # Compose the whole-income picture: earned income and dividends stack
    # below the gain and consume the basic-rate band; a relief-at-source
    # pension contribution extends the basic-rate limit for CGT as well.
    # (With no dividends and no pension this equals earned - PA, so the
    # simpler prior behaviour is preserved exactly.)
    composed = combined_personal_tax(
        {
            "earned_income": earned_income,
            "dividend_income": dividend_income,
            "gross_pension_contribution": gross_pension,
        },
        tax_year,
    )
    income_below_gain = composed["taxable_income_total"]

    aea_used = min(aea_param["amount"], gain)
    taxable_gain = round(gain - aea_used, 2)

    basic_rate_limit = bands_param["bands"][0]["upper"] + gross_pension
    basic_band_remaining = max(0.0, basic_rate_limit - income_below_gain)
    at_lower_rate = min(taxable_gain, basic_band_remaining)
    at_higher_rate = max(0.0, taxable_gain - at_lower_rate)
    tax_due = round(at_lower_rate * rates["lower"] + at_higher_rate * rates["higher"], 2)

    return {
        "chargeable_gain": gain,
        "asset_type": asset_type,
        "annual_exempt_amount_used": round(aea_used, 2),
        "taxable_gain": taxable_gain,
        "income_below_gain": income_below_gain,
        "basic_band_remaining_for_gain": round(basic_band_remaining, 2),
        "gain_at_lower_rate": round(at_lower_rate, 2),
        "gain_at_higher_rate": round(at_higher_rate, 2),
        "tax_due": tax_due,
    }


@register(
    "sdlt_residential",
    consumes=["sdlt.residential_bands"],
    description="SDLT on a residential purchase (England/NI): banded rates, the "
    "additional-dwellings surcharge (FA 2003 Sch 4ZA), and first-time buyers' "
    "relief (Sch 6ZA) with its price cap.",
)
def sdlt_residential(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts.get("price", 0)))
    additional = bool(facts.get("additional_dwelling", False))
    first_time_buyer = bool(facts.get("first_time_buyer", False))

    param = get_parameter("sdlt.residential_bands", tax_year)
    ftb = param["first_time_buyer"]

    ftb_relief_applies = first_time_buyer and not additional and price <= ftb["cap"]
    if ftb_relief_applies:
        banded = round(max(0.0, price - ftb["relief_threshold"]) * ftb["rate_above_threshold"], 2)
    else:
        banded = 0.0
        lower = 0.0
        for band in param["bands"]:
            upper = band["upper"] if band["upper"] is not None else price
            if price > lower:
                banded += (min(price, upper) - lower) * band["rate"]
            lower = upper
        banded = round(banded, 2)

    surcharge = round(price * param["additional_dwelling_surcharge"], 2) if additional else 0.0

    return {
        "price": price,
        "first_time_buyer_relief_applied": ftb_relief_applies,
        "banded_sdlt": banded,
        "additional_dwelling_surcharge": surcharge,
        "total_sdlt": round(banded + surcharge, 2),
    }


@register(
    "strategy.cgt_ppr_relief",
    consumes=[
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Private residence relief on disposal of a property that has been the "
    "main residence for part of the ownership period, including the final-9-months rule.",
)
def strategy_cgt_ppr_relief(facts: dict, tax_year: str) -> dict:
    gain = float(facts["disposal_gain"])
    ownership_months = max(1.0, float(facts.get("ownership_months", 1)))
    occupied_months = min(
        ownership_months, max(0.0, float(facts.get("occupied_as_main_residence_months", 0)))
    )
    earned_income = float(facts.get("earned_income", 0))
    dividend_income = float(facts.get("dividend_income", 0))

    # TCGA 1992 s.223(2): the final 9 months of ownership always qualify if
    # the property has at some time been the only or main residence.
    final_period = min(9.0, ownership_months - occupied_months) if occupied_months else 0.0
    exempt_months = min(ownership_months, occupied_months + final_period)
    exempt_fraction = exempt_months / ownership_months
    exempt_gain = round(gain * exempt_fraction, 2)
    chargeable_gain = round(gain - exempt_gain, 2)

    with_relief = cgt_liability(
        {"chargeable_gain": chargeable_gain, "asset_type": "residential",
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )
    without_relief = cgt_liability(
        {"chargeable_gain": gain, "asset_type": "residential",
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )

    return {
        "total_gain": gain,
        "ownership_months": ownership_months,
        "exempt_months_including_final_period": exempt_months,
        "exempt_gain": exempt_gain,
        "chargeable_gain_after_relief": chargeable_gain,
        "cgt_with_relief": with_relief["tax_due"],
        "cgt_without_relief": without_relief["tax_due"],
        "relief_saving": round(without_relief["tax_due"] - with_relief["tax_due"], 2),
    }


@register(
    "strategy.cgt_lettings_relief",
    consumes=[
        "cgt.lettings_relief",
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Lettings relief on a shared-occupancy let (TCGA 1992 s.223B): where part "
    "of the only or main residence is let as residential accommodation while the owner "
    "also occupies another part, the let-portion gain is relieved by the lowest of the "
    "letting gain, the private residence relief, and the 40,000 cap.",
)
def strategy_cgt_lettings_relief(facts: dict, tax_year: str) -> dict:
    """Post-6-April-2020 lettings relief: available ONLY where the owner
    shares occupancy with the tenant (TCGA 1992 s.223B; the pre-2020
    let-after-moving-out relief was withdrawn). Modelled as a space-based
    part-let of a residence occupied throughout ownership, with the let
    fraction an entered fact. Time-apportioned mixed occupation (letting for
    only part of the ownership period) is not composed in — see
    DEVELOPER_HANDOVER §5.
    """
    gain = max(0.0, float(facts["disposal_gain"]))
    let_fraction = min(1.0, max(0.0, float(facts.get("let_fraction", 0))))
    earned_income = float(facts.get("earned_income", 0))
    dividend_income = float(facts.get("dividend_income", 0))

    cap = get_parameter("cgt.lettings_relief", tax_year)["cap"]

    # PPR covers the owner-occupied part; the let part is chargeable but
    # reduced by lettings relief = lowest of (letting gain, PPR, cap).
    ppr_relief = round(gain * (1 - let_fraction), 2)
    letting_gain = round(gain * let_fraction, 2)
    lettings_relief = round(min(cap, ppr_relief, letting_gain), 2)
    chargeable = round(letting_gain - lettings_relief, 2)

    with_relief = cgt_liability(
        {"chargeable_gain": chargeable, "asset_type": "residential",
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )
    without_lettings = cgt_liability(
        {"chargeable_gain": letting_gain, "asset_type": "residential",
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )

    return {
        "total_gain": gain,
        "private_residence_relief": ppr_relief,
        "letting_gain": letting_gain,
        "lettings_relief": lettings_relief,
        "chargeable_gain_after_reliefs": chargeable,
        "cgt_due": with_relief["tax_due"],
        "cgt_without_lettings_relief": without_lettings["tax_due"],
        "lettings_relief_tax_saving": round(
            without_lettings["tax_due"] - with_relief["tax_due"], 2
        ),
    }


@register(
    "strategy.cgt_spousal_transfer_before_disposal",
    consumes=[
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="No-gain/no-loss transfer of a half share to a spouse before disposal "
    "(TCGA 1992 s.58): both annual exempt amounts and both basic-rate bands are used.",
)
def strategy_cgt_spousal_transfer(facts: dict, tax_year: str) -> dict:
    gain = float(facts["disposal_gain"])
    asset_type = facts.get("asset_type", "residential")
    earned_income = float(facts.get("earned_income", 0))
    dividend_income = float(facts.get("dividend_income", 0))
    spouse_earned_income = float(facts.get("spouse_earned_income", 0))
    spouse_dividend_income = float(facts.get("spouse_dividend_income", 0))

    alone = cgt_liability(
        {"chargeable_gain": gain, "asset_type": asset_type,
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )
    own_half = cgt_liability(
        {"chargeable_gain": gain / 2, "asset_type": asset_type,
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )
    spouse_half = cgt_liability(
        {"chargeable_gain": gain / 2, "asset_type": asset_type,
         "earned_income": spouse_earned_income, "dividend_income": spouse_dividend_income},
        tax_year,
    )
    split_total = round(own_half["tax_due"] + spouse_half["tax_due"], 2)

    return {
        "gain": gain,
        "cgt_disposing_alone": alone["tax_due"],
        "cgt_after_half_share_to_spouse": split_total,
        "own_half_cgt": own_half["tax_due"],
        "spouse_half_cgt": spouse_half["tax_due"],
        "saving": round(alone["tax_due"] - split_total, 2),
        # The transfer must be an outright gift before an unconditional
        # sale contract exists; anti-avoidance can bite on pre-arranged
        # same-day transfers with no change of beneficial ownership.
    }


@register(
    "strategy.cgt_business_asset_disposal_relief",
    consumes=[
        "cgt.business_asset_disposal_relief",
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Business Asset Disposal Relief (TCGA 1992 ss.169H-169N): qualifying "
    "gains up to the lifetime limit at the reduced BADR rate, any excess at the "
    "standard rate, compared with the same disposal taxed without the relief.",
)
def strategy_cgt_business_asset_disposal_relief(facts: dict, tax_year: str) -> dict:
    """Simplifications documented for editorial review (Section 5.6): BADR-
    qualifying gains are charged before other gains and, up to the 1,000,000
    lifetime limit, occupy the whole basic-rate band, so any qualifying gain
    *above* the limit is modelled at the standard higher rate for non-
    residential assets (24% in 2025/26) rather than band-split — correct
    whenever qualifying gains reach the basic-rate band, and conservative
    (never understating tax) otherwise. The annual exempt amount is set
    against the relieved gain, which is conservative where an unrelieved
    excess exists. Qualifying conditions (two-year ownership; 5% personal-
    company holding for shares) are assumed met — the eligibility of the
    disposal is a matter for the adviser, not this calculator.
    """
    gain = max(0.0, float(facts["disposal_gain"]))
    earned_income = max(0.0, float(facts.get("earned_income", 0)))
    dividend_income = max(0.0, float(facts.get("dividend_income", 0)))
    prior_badr_used = max(0.0, float(facts.get("badr_lifetime_limit_used", 0)))

    badr_param = get_parameter("cgt.business_asset_disposal_relief", tax_year)
    aea_param = get_parameter("cgt.annual_exempt_amount", tax_year)
    other_rates = get_parameter("cgt.rates", tax_year)["other"]

    badr_rate = badr_param["rate"]
    remaining_limit = max(0.0, badr_param["lifetime_limit"] - prior_badr_used)

    aea_used = min(aea_param["amount"], gain)
    taxable_gain = round(gain - aea_used, 2)

    at_badr_rate = min(taxable_gain, remaining_limit)
    above_limit = round(taxable_gain - at_badr_rate, 2)
    badr_tax = round(at_badr_rate * badr_rate, 2)
    excess_tax = round(above_limit * other_rates["higher"], 2)
    cgt_with_badr = round(badr_tax + excess_tax, 2)

    # The same disposal with no relief: a normal non-residential ("other")
    # gain, band-split against the client's whole income.
    without = cgt_liability(
        {"chargeable_gain": gain, "asset_type": "other",
         "earned_income": earned_income, "dividend_income": dividend_income},
        tax_year,
    )

    return {
        "qualifying_gain": gain,
        "annual_exempt_amount_used": round(aea_used, 2),
        "taxable_gain": taxable_gain,
        "remaining_lifetime_limit": round(remaining_limit, 2),
        "gain_at_badr_rate": round(at_badr_rate, 2),
        "badr_rate": badr_rate,
        "gain_above_lifetime_limit": above_limit,
        "cgt_with_badr": cgt_with_badr,
        "cgt_without_badr": without["tax_due"],
        "saving": round(without["tax_due"] - cgt_with_badr, 2),
    }


@register(
    "strategy.sdlt_purchase_planning",
    consumes=["sdlt.residential_bands"],
    description="SDLT cost of a planned residential purchase: banded charge, the 5% "
    "additional-dwellings surcharge exposure, and first-time buyers' relief.",
)
def strategy_sdlt_purchase(facts: dict, tax_year: str) -> dict:
    price = float(facts["price"])
    additional = bool(facts.get("additional_dwelling", False))
    first_time_buyer = bool(facts.get("first_time_buyer", False))

    as_planned = sdlt_residential(
        {"price": price, "additional_dwelling": additional, "first_time_buyer": first_time_buyer},
        tax_year,
    )
    without_surcharge = sdlt_residential(
        {"price": price, "additional_dwelling": False, "first_time_buyer": first_time_buyer},
        tax_year,
    )

    return {
        "as_planned": as_planned,
        "surcharge_cost_of_additional_dwelling": round(
            as_planned["total_sdlt"] - without_surcharge["total_sdlt"], 2
        ),
        # If the purchase replaces a main residence sold within 3 years,
        # the surcharge is refundable on the timeline in FA 2003 Sch 4ZA.
    }


# --- Devolved land transaction taxes: Scotland (LBTT) and Wales (LTT) ---------
#
# Scotland and Wales set their own rates and bands under devolved statutes
# (LBTT(S)A 2013 s.24; LTTA 2017 s.24), so the England/NI SDLT figures do not
# apply there. LBTT mirrors SDLT's shape (progressive bands + a flat
# Additional Dwelling Supplement + first-time buyer relief that raises the
# nil-rate band). Wales charges additional dwellings through a *separate*
# higher-rate band table rather than a flat surcharge, and has no first-time
# buyer relief.


def _progressive_tax(price: float, bands: list) -> float:
    """Sum each price slice at its band rate. ``bands`` is a list of
    ``{"upper": threshold_or_None, "rate": fraction}`` in ascending order;
    the final band uses ``upper: None`` for 'no ceiling'."""
    tax = 0.0
    lower = 0.0
    for band in bands:
        upper = band["upper"] if band["upper"] is not None else price
        if price > lower:
            tax += (min(price, upper) - lower) * band["rate"]
        lower = upper
    return round(tax, 2)


@register(
    "lbtt_residential",
    consumes=["lbtt.residential_bands"],
    description="Land and Buildings Transaction Tax on a Scottish residential purchase: "
    "progressive bands, the Additional Dwelling Supplement on the whole price for "
    "additional dwellings, and first-time buyer relief which raises the nil-rate band "
    "(LBTT(S)A 2013 s.24).",
)
def lbtt_residential(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts.get("price", 0)))
    additional = bool(facts.get("additional_dwelling", False))
    first_time_buyer = bool(facts.get("first_time_buyer", False))

    param = get_parameter("lbtt.residential_bands", tax_year)
    bands = param["bands"]

    # First-time buyer relief raises the 0% band to the FTB threshold; the
    # remaining bands are unchanged (worth up to 600 for buyers above it).
    ftb_applies = first_time_buyer and not additional
    if ftb_applies:
        threshold = param["first_time_buyer_nil_rate_threshold"]
        bands = [{"upper": threshold, "rate": 0.0}] + [
            b for b in bands if b["upper"] is None or b["upper"] > threshold
        ]

    banded = _progressive_tax(price, bands)
    supplement = (
        round(price * param["additional_dwelling_supplement"], 2) if additional else 0.0
    )

    return {
        "price": price,
        "first_time_buyer_relief_applied": ftb_applies,
        "banded_lbtt": banded,
        "additional_dwelling_supplement": supplement,
        "total_lbtt": round(banded + supplement, 2),
    }


@register(
    "ltt_residential",
    consumes=["ltt.residential_bands"],
    description="Land Transaction Tax on a Welsh residential purchase: the main "
    "residential bands, or the separate higher-rate bands where the purchase is an "
    "additional dwelling. Wales has no first-time buyer relief (LTTA 2017 s.24).",
)
def ltt_residential(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts.get("price", 0)))
    additional = bool(facts.get("additional_dwelling", False))

    param = get_parameter("ltt.residential_bands", tax_year)
    bands = param["higher_bands"] if additional else param["main_bands"]

    return {
        "price": price,
        "additional_dwelling": additional,
        "total_ltt": _progressive_tax(price, bands),
    }


@register(
    "strategy.lbtt_purchase_planning",
    consumes=["lbtt.residential_bands"],
    description="LBTT cost of a planned Scottish residential purchase: banded charge, the "
    "Additional Dwelling Supplement exposure, and first-time buyer relief.",
)
def strategy_lbtt_purchase(facts: dict, tax_year: str) -> dict:
    price = float(facts["price"])
    additional = bool(facts.get("additional_dwelling", False))
    first_time_buyer = bool(facts.get("first_time_buyer", False))

    as_planned = lbtt_residential(
        {"price": price, "additional_dwelling": additional, "first_time_buyer": first_time_buyer},
        tax_year,
    )
    without_supplement = lbtt_residential(
        {"price": price, "additional_dwelling": False, "first_time_buyer": first_time_buyer},
        tax_year,
    )

    return {
        "as_planned": as_planned,
        "supplement_cost_of_additional_dwelling": round(
            as_planned["total_lbtt"] - without_supplement["total_lbtt"], 2
        ),
    }


@register(
    "strategy.ltt_purchase_planning",
    consumes=["ltt.residential_bands"],
    description="LTT cost of a planned Welsh residential purchase: the main-rate charge "
    "and, where an additional dwelling, the extra cost of the separate higher-rate bands.",
)
def strategy_ltt_purchase(facts: dict, tax_year: str) -> dict:
    price = float(facts["price"])
    additional = bool(facts.get("additional_dwelling", False))

    as_planned = ltt_residential(
        {"price": price, "additional_dwelling": additional}, tax_year
    )
    at_main_rates = ltt_residential({"price": price, "additional_dwelling": False}, tax_year)

    return {
        "as_planned": as_planned,
        "additional_property_cost": round(
            as_planned["total_ltt"] - at_main_rates["total_ltt"], 2
        ),
    }


# Non-residential / mixed-use freehold purchases. All three regimes charge
# these on their own progressive bands, distinct from the residential rates
# and with no additional-dwelling surcharge or first-time buyer relief.
# Leases (charged on rent NPV) are out of scope — see DEVELOPER_HANDOVER §5.


@register(
    "strategy.sdlt_non_residential_purchase",
    consumes=["sdlt.non_residential_bands"],
    description="SDLT on a planned non-residential or mixed-use freehold purchase in "
    "England/NI: progressive bands (FA 2003 s.55).",
)
def strategy_sdlt_non_residential_purchase(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts["price"]))
    param = get_parameter("sdlt.non_residential_bands", tax_year)
    return {"price": price, "total_sdlt": _progressive_tax(price, param["bands"])}


@register(
    "strategy.lbtt_non_residential_purchase",
    consumes=["lbtt.non_residential_bands"],
    description="LBTT on a planned non-residential freehold purchase in Scotland: "
    "progressive bands (LBTT(S)A 2013 s.24).",
)
def strategy_lbtt_non_residential_purchase(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts["price"]))
    param = get_parameter("lbtt.non_residential_bands", tax_year)
    return {"price": price, "total_lbtt": _progressive_tax(price, param["bands"])}


@register(
    "strategy.ltt_non_residential_purchase",
    consumes=["ltt.non_residential_bands"],
    description="LTT on a planned non-residential freehold purchase in Wales: progressive "
    "bands (LTTA 2017 s.24).",
)
def strategy_ltt_non_residential_purchase(facts: dict, tax_year: str) -> dict:
    price = max(0.0, float(facts["price"]))
    param = get_parameter("ltt.non_residential_bands", tax_year)
    return {"price": price, "total_ltt": _progressive_tax(price, param["bands"])}


# Lease grants are charged on the net present value (NPV) of the rent over
# the term, discounted at the statutory temporal rate (3.5%), on each
# regime's own NPV bands. Modelled for a constant annual rent over a whole
# number of years; stepped/uncertain rent, the five-year highest-rent rule,
# any lease premium, and residential leases are out of scope
# (DEVELOPER_HANDOVER §5).


def _lease_rent_npv(annual_rent: float, term_years: int, discount_rate: float) -> float:
    """NPV of a constant annual rent: sum of rent / (1+d)^i for each year i
    of the term (FA 2003 Sch 5 / LBTT(S)A Sch 19 / LTTA method)."""
    return round(
        sum(annual_rent / (1 + discount_rate) ** i for i in range(1, term_years + 1)), 2
    )


def _lease_charge(facts: dict, param: dict) -> dict:
    rent = max(0.0, float(facts["annual_rent"]))
    term = int(facts["term_years"])
    npv = _lease_rent_npv(rent, term, param["discount_rate"])
    return {
        "annual_rent": rent,
        "term_years": term,
        "net_present_value": npv,
        "tax_on_rent": _progressive_tax(npv, param["bands"]),
    }


@register(
    "strategy.sdlt_lease_npv",
    consumes=["sdlt.lease_npv_bands"],
    description="SDLT on the grant of a non-residential lease in England/NI: the net "
    "present value of the rent over the term at the 3.5% temporal discount rate, charged "
    "on the NPV bands (FA 2003 s.55, Schedule 5).",
)
def strategy_sdlt_lease_npv(facts: dict, tax_year: str) -> dict:
    result = _lease_charge(facts, get_parameter("sdlt.lease_npv_bands", tax_year))
    result["total_sdlt"] = result.pop("tax_on_rent")
    return result


@register(
    "strategy.lbtt_lease_npv",
    consumes=["lbtt.lease_npv_bands"],
    description="LBTT on the grant of a lease in Scotland: the net present value of the "
    "rent at the 3.5% discount rate, charged on the NPV bands (LBTT(S)A 2013 s.24, "
    "Schedule 19). Scotland also requires 3-yearly LBTT lease reviews (not modelled).",
)
def strategy_lbtt_lease_npv(facts: dict, tax_year: str) -> dict:
    result = _lease_charge(facts, get_parameter("lbtt.lease_npv_bands", tax_year))
    result["total_lbtt"] = result.pop("tax_on_rent")
    return result


@register(
    "strategy.ltt_lease_npv",
    consumes=["ltt.lease_npv_bands"],
    description="LTT on the grant of a non-residential lease in Wales: the net present "
    "value of the rent at the 3.5% discount rate, charged on the NPV bands (LTTA 2017 "
    "s.24). Wales does not charge LTT on residential lease rent.",
)
def strategy_ltt_lease_npv(facts: dict, tax_year: str) -> dict:
    result = _lease_charge(facts, get_parameter("ltt.lease_npv_bands", tax_year))
    result["total_ltt"] = result.pop("tax_on_rent")
    return result


# --- Inheritance tax ----------------------------------------------------------


@register(
    "iht_estate_liability",
    consumes=["iht.nil_rate_band", "iht.residence_nil_rate_band", "iht.rates"],
    description="IHT on a death estate: spouse and charity exemptions, nil-rate band with "
    "transferred fraction, residence nil-rate band with taper and home-value cap, and the "
    "36% reduced-rate test for charitable legacies.",
)
def iht_estate_liability(facts: dict, tax_year: str) -> dict:
    """Simplifications documented for editorial review (Section 5.6): the
    36% baseline amount is (net estate - spouse exemption - NRB), ignoring
    RNRB in line with HMRC guidance but without the full Schedule 1A
    component-by-component split; no BPR/APR, settled property, foreign
    property, or grossing-up of tax-free legacies (IHTA 1984 s.38).
    """
    gross = max(0.0, float(facts.get("gross_estate_value", 0)))
    liabilities = max(0.0, float(facts.get("liabilities", 0)))
    estate = max(0.0, round(gross - liabilities, 2))

    to_spouse = min(max(0.0, float(facts.get("amount_to_spouse", 0))), estate)
    charity = min(max(0.0, float(facts.get("charitable_legacy", 0))), estate - to_spouse)
    chargeable_estate = round(estate - to_spouse - charity, 2)

    nrb_param = get_parameter("iht.nil_rate_band", tax_year)
    rnrb_param = get_parameter("iht.residence_nil_rate_band", tax_year)
    rates = get_parameter("iht.rates", tax_year)

    transferred_nrb = min(max(float(facts.get("transferred_nrb_fraction", 0)), 0.0), 1.0)
    nrb = round(nrb_param["amount"] * (1 + transferred_nrb), 2)

    rnrb = 0.0
    home_equity = max(0.0, float(facts.get("home_equity_value", 0)))
    if facts.get("home_passes_to_direct_descendants") and home_equity > 0:
        transferred_rnrb = min(max(float(facts.get("transferred_rnrb_fraction", 0)), 0.0), 1.0)
        base_rnrb = rnrb_param["amount"] * (1 + transferred_rnrb)
        taper_excess = max(0.0, estate - rnrb_param["taper_threshold"])
        base_rnrb = max(0.0, base_rnrb - taper_excess * rnrb_param["taper_rate"])
        rnrb = round(min(base_rnrb, home_equity), 2)

    taxable = max(0.0, round(chargeable_estate - nrb - rnrb, 2))

    baseline = max(0.0, round(estate - to_spouse - nrb, 2))
    qualifies_reduced = (
        taxable > 0 and charity >= rates["charity_baseline_fraction"] * baseline
    )
    rate = rates["reduced_charity_rate"] if qualifies_reduced else rates["death_rate"]

    return {
        "net_estate": estate,
        "spouse_exempt": round(to_spouse, 2),
        "charitable_legacy": round(charity, 2),
        "chargeable_estate": chargeable_estate,
        "nil_rate_band": nrb,
        "residence_nil_rate_band": rnrb,
        "taxable_amount": taxable,
        "rate_applied": rate,
        "qualifies_reduced_charity_rate": qualifies_reduced,
        "charity_baseline_amount": baseline,
        "tax_due": round(taxable * rate, 2),
    }


@register(
    "strategy.iht_spousal_transfer_nil_rate_bands",
    consumes=["iht.nil_rate_band", "iht.residence_nil_rate_band", "iht.rates"],
    description="Quantifies the spouse exemption on first death and the value of claiming "
    "transferred NRB and RNRB on the survivor's death.",
)
def strategy_iht_spousal_nil_rate_bands(facts: dict, tax_year: str) -> dict:
    combined = float(facts["combined_estate_second_death"])
    home_equity = float(facts.get("combined_home_equity_second_death", 0))
    to_descendants = bool(facts.get("home_passes_to_direct_descendants", False))

    common = {
        "gross_estate_value": combined,
        "home_equity_value": home_equity,
        "home_passes_to_direct_descendants": to_descendants,
    }
    with_claims = iht_estate_liability(
        {**common, "transferred_nrb_fraction": 1, "transferred_rnrb_fraction": 1}, tax_year
    )
    without_claims = iht_estate_liability(common, tax_year)

    rnrb_param = get_parameter("iht.residence_nil_rate_band", tax_year)
    return {
        # Transfers between UK-domiciled spouses/civil partners are wholly
        # exempt (IHTA 1984 s.18), so a full first-death spousal transfer
        # produces no tax and preserves both nil-rate bands for transfer.
        "first_death_tax_with_full_spouse_exemption": 0.0,
        "second_death_with_transferred_bands": with_claims,
        "second_death_without_claims": without_claims,
        "value_of_transferable_bands": round(
            without_claims["tax_due"] - with_claims["tax_due"], 2
        ),
        "rnrb_taper_applies": combined > rnrb_param["taper_threshold"],
    }


@register(
    "strategy.iht_lifetime_gifting",
    consumes=[
        "iht.nil_rate_band",
        "iht.residence_nil_rate_band",
        "iht.rates",
        "iht.gift_exemptions",
    ],
    description="Lifetime gifting: annual exemptions, the PET seven-year clock, taper relief "
    "schedule, and the estate tax saved if the donor survives seven years.",
)
def strategy_iht_lifetime_gifting(facts: dict, tax_year: str) -> dict:
    gift = float(facts["planned_gift"])
    estate_basis = float(facts["estate_basis_value"])

    gifts_param = get_parameter("iht.gift_exemptions", tax_year)
    exemption_available = gifts_param["annual_exemption"] * (
        2 if facts.get("prior_year_annual_exemption_unused") else 1
    )
    exempt_amount = round(min(gift, exemption_available), 2)
    pet_amount = round(gift - exempt_amount, 2)

    base_facts = {
        "gross_estate_value": estate_basis,
        "home_equity_value": facts.get("home_equity_value", 0),
        "home_passes_to_direct_descendants": facts.get("home_passes_to_direct_descendants", False),
        "transferred_nrb_fraction": facts.get("transferred_nrb_fraction", 0),
        "transferred_rnrb_fraction": facts.get("transferred_rnrb_fraction", 0),
    }
    before = iht_estate_liability(base_facts, tax_year)
    after = iht_estate_liability(
        {**base_facts, "gross_estate_value": estate_basis - gift}, tax_year
    )

    return {
        "planned_gift": round(gift, 2),
        "immediately_exempt_amount": exempt_amount,
        "pet_amount": pet_amount,
        "estate_tax_before_gift": before["tax_due"],
        "estate_tax_if_survive_7_years": after["tax_due"],
        "saving_if_survive_7_years": round(before["tax_due"] - after["tax_due"], 2),
        # Taper relief reduces the TAX on a failed PET (death in years 3-7),
        # and only where the PET exceeds the NRB; it never reduces the PET
        # itself (IHTA 1984 s.7(4)).
        "taper_relief_schedule": gifts_param["taper_relief"],
    }


@register(
    "strategy.iht_charitable_legacy_reduced_rate",
    consumes=["iht.nil_rate_band", "iht.residence_nil_rate_band", "iht.rates"],
    description="Charitable legacy at or above 10% of the baseline amount: the whole taxable "
    "estate is charged at 36% instead of 40% (IHTA 1984 Sch 1A).",
)
def strategy_iht_charitable_legacy(facts: dict, tax_year: str) -> dict:
    estate_basis = float(facts["estate_basis_value"])
    current_charity = float(facts.get("current_charitable_legacy", 0))

    rates = get_parameter("iht.rates", tax_year)
    base_facts = {
        "gross_estate_value": estate_basis,
        "home_equity_value": facts.get("home_equity_value", 0),
        "home_passes_to_direct_descendants": facts.get("home_passes_to_direct_descendants", False),
        "transferred_nrb_fraction": facts.get("transferred_nrb_fraction", 0),
        "transferred_rnrb_fraction": facts.get("transferred_rnrb_fraction", 0),
        "charitable_legacy": current_charity,
    }
    current = iht_estate_liability(base_facts, tax_year)
    target_legacy = round(
        current["charity_baseline_amount"] * rates["charity_baseline_fraction"], 2
    )

    result = {
        "estate_taxable": current["taxable_amount"] > 0,
        "current_charitable_legacy": round(current_charity, 2),
        "target_legacy_for_reduced_rate": target_legacy,
        "current_position": current,
    }
    if current["qualifies_reduced_charity_rate"] or current_charity >= target_legacy:
        result["already_qualifies"] = True
        return result

    with_target = iht_estate_liability(
        {**base_facts, "charitable_legacy": target_legacy}, tax_year
    )
    extra_legacy = round(target_legacy - current_charity, 2)
    tax_saving = round(current["tax_due"] - with_target["tax_due"], 2)
    result.update(
        {
            "already_qualifies": False,
            "position_at_target_legacy": with_target,
            "extra_charitable_legacy_needed": extra_legacy,
            "tax_saving": tax_saving,
            "net_cost_to_beneficiaries": round(extra_legacy - tax_saving, 2),
        }
    )
    return result
