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
from .taxyear import next_tax_year


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


def _class4_nic(profit: float, tax_year: str) -> float:
    """Class 4 NIC on self-employed / partnership trading profit."""
    p = get_parameter("national_insurance.class4", tax_year)
    lpl, upl, rate, upper_rate = (
        p["lower_profits_limit"], p["upper_profits_limit"], p["rate"], p["upper_rate"],
    )
    profit = max(0.0, float(profit))
    return round(
        max(0.0, min(profit, upl) - lpl) * rate + max(0.0, profit - upl) * upper_rate, 2
    )


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
    "strategy.payroll_giving",
    consumes=[
        "income_tax.bands",
        "income_tax.personal_allowance",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Payroll Giving (ITEPA 2003 Part 12 ss.713-715): a donation deducted from "
    "pay before PAYE is applied, so the donor gets full relief at their marginal rate with "
    "no grossing-up or claim, and the charity receives the whole amount. National Insurance "
    "is still due on the donated pay — the scheme relieves income tax only.",
)
def strategy_payroll_giving(facts: dict, tax_year: str) -> dict:
    earned = max(0.0, float(facts.get("earned_income", 0)))
    dividends = max(0.0, float(facts.get("dividend_income", 0)))
    donation = min(max(0.0, float(facts.get("annual_donation", 0))), earned)

    baseline = combined_personal_tax(
        {"earned_income": earned, "dividend_income": dividends}, tax_year
    )
    with_donation = combined_personal_tax(
        {"earned_income": earned - donation, "dividend_income": dividends}, tax_year
    )
    tax_saved = round(baseline["total_tax"] - with_donation["total_tax"], 2)

    return {
        "annual_donation": round(donation, 2),
        "charity_receives": round(donation, 2),
        "income_tax_saved": tax_saved,
        "net_cost_to_donor": round(donation - tax_saved, 2),
        "personal_allowance_restored": round(
            with_donation["personal_allowance"] - baseline["personal_allowance"], 2
        ),
    }


@register(
    "strategy.income_timing",
    consumes=[
        "income_tax.bands",
        "income_tax.personal_allowance",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Timing of income across tax years: compares the incremental tax on a "
    "controllable amount of income (a bonus under the ITEPA 2003 s.18 receipts basis, or a "
    "dividend charged for the year it is paid, ITTOIA 2005 ss.383-384) landing in the "
    "current tax year against the following one, using each year's own released rates and "
    "the client's expected income position in each year.",
)
def strategy_income_timing(facts: dict, tax_year: str) -> dict:
    amount = max(0.0, float(facts.get("shiftable_amount", 0)))
    income_type = facts.get("income_type", "dividend")
    this_earned = max(0.0, float(facts.get("earned_income", 0)))
    this_dividends = max(0.0, float(facts.get("dividend_income", 0)))
    later_year = next_tax_year(tax_year)
    next_earned = max(0.0, float(facts.get("next_year_earned_income", this_earned)))
    next_dividends = max(0.0, float(facts.get("next_year_dividend_income", this_dividends)))

    def incremental_tax(year: str, base_earned: float, base_dividends: float) -> float:
        base = combined_personal_tax(
            {"earned_income": base_earned, "dividend_income": base_dividends}, year
        )
        if income_type == "dividend":
            loaded = combined_personal_tax(
                {"earned_income": base_earned, "dividend_income": base_dividends + amount},
                year,
            )
        else:
            loaded = combined_personal_tax(
                {"earned_income": base_earned + amount, "dividend_income": base_dividends},
                year,
            )
        return round(loaded["total_tax"] - base["total_tax"], 2)

    tax_if_this_year = incremental_tax(tax_year, this_earned, this_dividends)
    tax_if_next_year = incremental_tax(later_year, next_earned, next_dividends)

    if tax_if_this_year < tax_if_next_year:
        recommendation = "take_this_year"
    elif tax_if_next_year < tax_if_this_year:
        recommendation = "defer_to_next_year"
    else:
        recommendation = "indifferent"

    return {
        "shiftable_amount": round(amount, 2),
        "income_type": income_type,
        "this_tax_year": tax_year,
        "next_tax_year": later_year,
        "incremental_tax_this_year": tax_if_this_year,
        "incremental_tax_next_year": tax_if_next_year,
        "recommendation": recommendation,
        "saving": round(abs(tax_if_this_year - tax_if_next_year), 2),
    }


@register(
    "strategy.charity_gift_of_assets",
    consumes=[
        "income_tax.bands",
        "income_tax.personal_allowance",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "cgt.annual_exempt_amount",
        "cgt.rates",
    ],
    description="Gift of qualifying shares/securities or land to charity: the market value "
    "is deducted from net income (ITA 2007 s.431), giving relief at the donor's marginal "
    "rate, and the disposal is no-gain/no-loss (TCGA 1992 s.257), so any held gain escapes "
    "CGT entirely. The deduction is modelled against earned income first, then dividends "
    "(the standard order); the CGT avoided is what a market-value sale would have cost "
    "given the client's income composition.",
)
def strategy_charity_gift_of_assets(facts: dict, tax_year: str) -> dict:
    gift_value = max(0.0, float(facts.get("gift_value", 0)))
    held_gain = max(0.0, float(facts.get("held_gain", 0)))
    asset_type = facts.get("asset_type", "other")
    earned = max(0.0, float(facts.get("earned_income", 0)))
    dividends = max(0.0, float(facts.get("dividend_income", 0)))

    baseline = combined_personal_tax(
        {"earned_income": earned, "dividend_income": dividends}, tax_year
    )
    relieved_earned = max(0.0, earned - gift_value)
    remainder = max(0.0, gift_value - earned)
    relieved_dividends = max(0.0, dividends - remainder)
    with_relief = combined_personal_tax(
        {"earned_income": relieved_earned, "dividend_income": relieved_dividends}, tax_year
    )
    income_tax_saved = round(baseline["total_tax"] - with_relief["total_tax"], 2)

    cgt_if_sold = cgt_liability(
        {
            "chargeable_gain": held_gain,
            "asset_type": asset_type,
            "earned_income": earned,
            "dividend_income": dividends,
        },
        tax_year,
    )
    cgt_avoided = cgt_if_sold["tax_due"]

    return {
        "gift_value": round(gift_value, 2),
        "held_gain": round(held_gain, 2),
        "income_tax_saved": income_tax_saved,
        "cgt_avoided": cgt_avoided,
        "total_tax_benefit": round(income_tax_saved + cgt_avoided, 2),
        "net_cost_of_gift": round(gift_value - income_tax_saved, 2),
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
    "strategy.salary_sacrifice",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "national_insurance.employee_class1",
        "national_insurance.employer_class1",
    ],
    description="Salary sacrifice into an employer pension: giving up salary cuts the "
    "employee's income tax and Class 1 NIC and the employer's secondary NIC, and the whole "
    "sacrificed amount goes into the pension gross. Quantifies the employee saving, the "
    "employer NIC saving, the amount into the pension and its net cost to the employee.",
)
def strategy_salary_sacrifice(facts: dict, tax_year: str) -> dict:
    salary = max(0.0, float(facts.get("salary", 0)))
    sacrifice = min(salary, max(0.0, float(facts.get("sacrifice_amount", 0))))
    reduced = round(salary - sacrifice, 2)

    def _cost(gross: float) -> tuple:
        it = income_tax_on_earned_income({"total_income": gross}, tax_year)["tax_due"]
        ee = employee_class1_nic({"annual_salary": gross}, tax_year)["nic_due"]
        er = employer_class1_nic(
            {"annual_salary": gross, "employment_allowance_available": False}, tax_year
        )["nic_due"]
        return it, ee, er

    it0, ee0, er0 = _cost(salary)
    it1, ee1, er1 = _cost(reduced)

    employee_saved = round((it0 + ee0) - (it1 + ee1), 2)
    employer_ni_saved = round(er0 - er1, 2)

    return {
        "salary_sacrificed": round(sacrifice, 2),
        "employee_income_tax_and_ni_saved": employee_saved,
        "employer_ni_saved": employer_ni_saved,
        "into_pension": round(sacrifice, 2),
        "net_cost_of_pension_to_employee": round(sacrifice - employee_saved, 2),
        "total_saving": round(employee_saved + employer_ni_saved, 2),
    }


@register(
    "strategy.termination_payment",
    consumes=[
        "termination_payment.exemption",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "national_insurance.employer_class1",
    ],
    description="Taxation of a termination payment (ITEPA 2003 ss.401-403): the first "
    "£30,000 of a qualifying (non-contractual) termination payment is exempt from income "
    "tax; the excess is taxed as the top slice of the employee's income, and the employer "
    "pays Class 1A NIC on that excess (SSCBA 1992 s.10). Any post-employment notice pay "
    "(PENP) and contractual sums are taxed in full as earnings and must be excluded from "
    "the figure passed in as the qualifying payment.",
)
def strategy_termination_payment(facts: dict, tax_year: str) -> dict:
    """Termination-payment tax. The ``termination_payment`` passed in is the
    *qualifying* s.401 amount only — PENP (s.402D) and contractual pay are
    taxed in full as ordinary earnings and are surfaced as an intake question,
    not silently swept into the exemption. The excess over the £30,000
    exemption is taxed as the top slice: on top of the employee's other income,
    which also captures any personal-allowance taper the payment triggers.
    """
    payment = max(0.0, float(facts.get("termination_payment", 0)))
    other_income = max(0.0, float(facts.get("other_income", 0)))

    exemption = get_parameter("termination_payment.exemption", tax_year)["amount"]
    exempt_amount = round(min(payment, exemption), 2)
    taxable_excess = round(max(0.0, payment - exemption), 2)

    # Income tax on the excess as the top slice of income (marginal: the tax on
    # other income + excess, less the tax on other income alone).
    tax_with = income_tax_on_earned_income({"total_income": other_income + taxable_excess}, tax_year)["tax_due"]
    tax_without = income_tax_on_earned_income({"total_income": other_income}, tax_year)["tax_due"]
    income_tax_on_excess = round(tax_with - tax_without, 2)

    # Employer Class 1A NIC on the excess (charged at the secondary Class 1 rate;
    # the £30,000 exemption already removes the exempt slice, so no further
    # threshold applies). This is an employer cost, not the employee's.
    secondary_rate = get_parameter("national_insurance.employer_class1", tax_year)["rate"]
    employer_class1a_nic = round(taxable_excess * secondary_rate, 2)

    # The employee bears the income tax only (no employee NIC on termination payments).
    net_to_employee = round(payment - income_tax_on_excess, 2)

    return {
        "termination_payment": round(payment, 2),
        "exempt_amount": exempt_amount,
        "taxable_excess": taxable_excess,
        "income_tax_on_excess": income_tax_on_excess,
        "employer_class1a_nic": employer_class1a_nic,
        "net_to_employee": net_to_employee,
        "total_employer_cost": round(payment + employer_class1a_nic, 2),
    }


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
    "strategy.directors_loan_s455",
    consumes=["directors_loan.s455"],
    description="Directors' loan account: the s.455 charge (CTA 2010 s.455) — a temporary "
    "corporation-tax charge on the amount of a loan to a participator still outstanding 9 "
    "months and 1 day after the accounting period end. It is refunded (s.458) when the loan "
    "is repaid, so repaying within the window avoids it entirely.",
)
def strategy_directors_loan_s455(facts: dict, tax_year: str) -> dict:
    balance = max(0.0, float(facts.get("overdrawn_loan_balance", 0)))
    repaid_in_time = min(balance, max(0.0, float(facts.get("repaid_within_9_months", 0))))

    param = get_parameter("directors_loan.s455", tax_year)
    rate = param["rate"]

    outstanding = round(balance - repaid_in_time, 2)
    charge = round(outstanding * rate, 2)
    charge_if_none_repaid = round(balance * rate, 2)

    return {
        "overdrawn_loan_balance": round(balance, 2),
        "repaid_within_9_months": round(repaid_in_time, 2),
        "outstanding_after_deadline": outstanding,
        "s455_charge": charge,
        "charge_avoided_by_repaying_in_time": round(charge_if_none_repaid - charge, 2),
        # A beneficial-loan benefit-in-kind can also arise above the threshold.
        "beneficial_loan_reportable": balance > param["beneficial_loan_threshold"],
    }


@register(
    "strategy.capital_allowances",
    consumes=["capital_allowances.aia", "corporation_tax.rates"],
    description="Capital allowances on qualifying plant and machinery (CAA 2001): the Annual "
    "Investment Allowance gives 100% relief on spend up to the AIA limit; spend above it "
    "enters the main pool at the 18% writing-down allowance. Shows the first-year deduction "
    "and the tax it saves at the client's marginal rate (defaulting to the CT main rate).",
)
def strategy_capital_allowances(facts: dict, tax_year: str) -> dict:
    spend = max(0.0, float(facts.get("qualifying_spend", 0)))
    param = get_parameter("capital_allowances.aia", tax_year)
    ct_param = get_parameter("corporation_tax.rates", tax_year)
    marginal_rate = float(facts.get("marginal_rate", ct_param["main_rate"]))

    aia_used = min(spend, param["aia_limit"])
    above_aia = round(spend - aia_used, 2)
    written_down = round(above_aia * param["main_pool_wda"], 2)
    first_year_allowance = round(aia_used + written_down, 2)
    tax_saved = round(first_year_allowance * marginal_rate, 2)

    return {
        "qualifying_spend": round(spend, 2),
        "annual_investment_allowance_used": round(aia_used, 2),
        "written_down_first_year": written_down,
        "first_year_allowance": first_year_allowance,
        "marginal_rate": marginal_rate,
        "tax_saved_year_one": tax_saved,
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
    "strategy.personal_pension_contribution",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Standalone recommendation to make a personal pension contribution (relief at "
    "source). Quantifies the basic-rate credit HMRC adds to the pot, the higher-rate and "
    "personal-allowance-taper relief given through band extension, the effective relief rate "
    "(up to 60% inside the 100,000-125,140 taper) and the net cost to the member. Relief is "
    "capped at the greater of 3,600 and relevant UK earnings (FA 2004 s.190) — dividends and "
    "savings/rental income do not count towards that cap.",
)
def strategy_personal_pension_contribution(facts: dict, tax_year: str) -> dict:
    earned = float(facts.get("earned_income", 0))
    dividends = float(facts.get("dividend_income", 0))
    desired = max(0.0, float(facts.get("desired_contribution", 0)))
    relevant_earnings = float(facts.get("relevant_uk_earnings", earned))

    relievable = min(desired, max(3600.0, relevant_earnings))
    unrelieved = round(desired - relievable, 2)
    basic_rate = get_parameter("income_tax.bands", tax_year)["bands"][0]["rate"]
    basic_credit = round(relievable * basic_rate, 2)

    without = combined_personal_tax(
        {"earned_income": earned, "dividend_income": dividends}, tax_year
    )
    with_contribution = combined_personal_tax(
        {
            "earned_income": earned,
            "dividend_income": dividends,
            "gross_pension_contribution": relievable,
        },
        tax_year,
    )
    personal_saving = round(without["total_tax"] - with_contribution["total_tax"], 2)
    pa_restored = round(
        with_contribution["personal_allowance"] - without["personal_allowance"], 2
    )
    total_relief = round(basic_credit + personal_saving, 2)
    net_cost = round(relievable - total_relief, 2)
    effective_rate = round(total_relief / relievable, 4) if relievable else 0.0

    return {
        "relievable_gross": round(relievable, 2),
        "unrelieved_amount": unrelieved,
        "basic_rate_credit_to_pension": basic_credit,
        "higher_rate_and_taper_saving": personal_saving,
        "personal_allowance_restored": pa_restored,
        "total_relief_value": total_relief,
        "effective_relief_rate": effective_rate,
        "net_cost_to_member": net_cost,
    }


@register(
    "strategy.employer_pension_contribution",
    consumes=["corporation_tax.rates", "national_insurance.employer_class1"],
    description="Standalone recommendation for a company to make an employer pension "
    "contribution instead of extra salary. There is no relevant-earnings cap and no NICs; the "
    "company gets a corporation-tax deduction (subject to the wholly-and-exclusively test, "
    "CTA 2009 s.54 — the reviewing accountant owns that judgement). Quantifies the corporation "
    "tax saved, the employer NIC saved versus paying the same amount as salary, and the net "
    "cost to the company.",
)
def strategy_employer_pension_contribution(facts: dict, tax_year: str) -> dict:
    profit = max(0.0, float(facts.get("company_profit", 0)))
    requested = max(0.0, float(facts.get("contribution", 0)))
    contribution = min(profit, requested) if profit > 0 else requested

    ct_before = corporation_tax({"taxable_profit": profit}, tax_year)["tax_due"]
    ct_after = corporation_tax(
        {"taxable_profit": max(0.0, profit - contribution)}, tax_year
    )["tax_due"]
    ct_saving = round(ct_before - ct_after, 2)

    secondary_rate = get_parameter("national_insurance.employer_class1", tax_year)["rate"]
    employer_ni_saved = round(contribution * secondary_rate, 2)
    net_cost = round(contribution - ct_saving, 2)

    return {
        "contribution": round(contribution, 2),
        "corporation_tax_saving": ct_saving,
        "employer_ni_saved_vs_salary": employer_ni_saved,
        "no_relevant_earnings_cap": True,
        "net_cost_to_company": net_cost,
    }


@register(
    "strategy.group_loss_relief",
    consumes=["corporation_tax.rates"],
    description="Group relief (CTA 2010 Part 5): a loss-making group company surrenders its "
    "current-period loss to a profitable 75%-group company, which sets it against its profits. "
    "The loss is relieved at the claimant's marginal rate — worth 26.5% where the claimant sits "
    "in the marginal-relief band, more than the 25% main rate or a 19%/main-rate carry-forward. "
    "Quantifies the corporation tax saved, the profit relieved, and any loss left to carry "
    "forward. The 75% group relationship is a precondition the reviewing accountant confirms.",
)
def strategy_group_loss_relief(facts: dict, tax_year: str) -> dict:
    loss = max(0.0, float(facts.get("surrendering_company_loss", 0)))
    profit = max(0.0, float(facts.get("claimant_company_profit", 0)))
    associated = int(facts.get("associated_companies", 0))

    relief_used = min(loss, profit)
    ct_args = {"associated_companies": associated}
    ct_before = corporation_tax({"taxable_profit": profit, **ct_args}, tax_year)["tax_due"]
    ct_after = corporation_tax(
        {"taxable_profit": profit - relief_used, **ct_args}, tax_year
    )["tax_due"]
    tax_saved = round(ct_before - ct_after, 2)
    unrelieved = round(loss - relief_used, 2)
    effective_rate = round(tax_saved / relief_used, 4) if relief_used else 0.0

    return {
        "loss_surrendered": round(relief_used, 2),
        "claimant_profit_before": round(profit, 2),
        "claimant_profit_after": round(profit - relief_used, 2),
        "corporation_tax_saved": tax_saved,
        "unrelieved_loss_carried_forward": unrelieved,
        "effective_relief_rate": effective_rate,
    }


@register(
    "strategy.isa_bed_and_isa",
    consumes=[
        "isa.allowance",
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "dividend_tax.bands",
    ],
    description="Bed-and-ISA: sell unwrapped investments — realising a gain that, kept within "
    "the CGT annual exempt amount, bears no CGT — and repurchase them inside an ISA so future "
    "dividends and growth are tax-free. Quantifies the amount sheltered (capped at the ISA "
    "subscription limit), any CGT crystallised on the transfer, and the annual dividend tax "
    "saved once the holding is inside the ISA (ITTOIA 2005 s.694; TCGA 1992 s.151). Future "
    "capital growth is also CGT-free but is not projected here (it depends on the growth rate).",
)
def strategy_isa_bed_and_isa(facts: dict, tax_year: str) -> dict:
    isa_limit = get_parameter("isa.allowance", tax_year)["amount"]
    aea = get_parameter("cgt.annual_exempt_amount", tax_year)["amount"]
    cgt_rates = get_parameter("cgt.rates", tax_year)["other"]
    div_bands = get_parameter("dividend_tax.bands", tax_year)["bands"]

    is_higher = bool(facts.get("is_higher_rate", True))
    amount = max(0.0, float(facts.get("amount_to_shelter", 0)))
    realised_gain = max(0.0, float(facts.get("realised_gain", 0)))
    aea_already_used = max(0.0, float(facts.get("aea_already_used", 0)))
    annual_dividends = max(0.0, float(facts.get("annual_dividend_income", 0)))

    sheltered = min(amount, isa_limit)
    aea_remaining = max(0.0, aea - aea_already_used)
    taxable_gain_now = max(0.0, realised_gain - aea_remaining)
    cgt_rate = cgt_rates["higher"] if is_higher else cgt_rates["lower"]
    cgt_now = round(taxable_gain_now * cgt_rate, 2)

    div_rate = div_bands[1]["rate"] if is_higher else div_bands[0]["rate"]
    annual_dividend_tax_saved = round(annual_dividends * div_rate, 2)

    return {
        "amount_sheltered": round(sheltered, 2),
        "isa_allowance_remaining": round(isa_limit - sheltered, 2),
        "gain_covered_by_exemption": round(min(realised_gain, aea_remaining), 2),
        "cgt_payable_on_transfer": cgt_now,
        "annual_dividend_tax_saved": annual_dividend_tax_saved,
    }


@register(
    "strategy.business_property_relief",
    consumes=["iht.business_property_relief", "iht.rates"],
    description="Business Property Relief / Agricultural Property Relief on death: qualifying "
    "business and agricultural property is relieved from inheritance tax at 100%, but from "
    "6 April 2026 the 100% rate is capped at a combined £1,000,000, with 50% relief on the "
    "excess (Finance Act 2025). Quantifies the value relieved, the taxable value remaining, and "
    "the IHT saved — and, run across the tax-year boundary, shows the extra IHT the reformed cap "
    "costs. Assumes the estate is otherwise above the nil-rate band (IHTA 1984 ss.103-124C).",
)
def strategy_business_property_relief(facts: dict, tax_year: str) -> dict:
    as_of = facts.get("as_of")
    param = get_parameter("iht.business_property_relief", tax_year, as_of=as_of)
    death_rate = get_parameter("iht.rates", tax_year, as_of=as_of)["death_rate"]

    value = max(0.0, float(facts.get("qualifying_value", 0)))
    cap = param["full_relief_cap"]
    rate_above = param["rate_above_cap"]

    if cap is None:
        value_at_full = value
        value_above_cap = 0.0
    else:
        value_at_full = min(value, cap)
        value_above_cap = max(0.0, value - cap)

    relieved = round(value_at_full + value_above_cap * rate_above, 2)
    taxable_after = round(value - relieved, 2)
    iht_saved = round(relieved * death_rate, 2)

    return {
        "qualifying_value": round(value, 2),
        "full_relief_cap": cap,
        "value_relieved_at_100pc": round(value_at_full, 2),
        "value_above_cap": round(value_above_cap, 2),
        "total_relieved_value": relieved,
        "taxable_value_after_relief": taxable_after,
        "iht_saved_by_relief": iht_saved,
    }


@register(
    "strategy.property_income_finance_cost",
    consumes=[
        "property_income.finance_cost_restriction",
        "income_tax.personal_allowance",
        "income_tax.bands",
    ],
    description="The s.24 residential-landlord finance-cost restriction: mortgage interest is no "
    "longer deducted from rental profit but relieved only as a 20% basic-rate tax reducer (on the "
    "lower of the finance costs, the rental profit and adjusted total income above the personal "
    "allowance). For a higher or additional-rate landlord this costs more tax than a full "
    "deduction would. Quantifies the rental profit, the tax reducer, the tax under the restriction "
    "versus full deductibility, and the extra tax the restriction costs — the figure that drives "
    "the incorporation question, since a company still deducts the interest in full. "
    "ITTOIA 2005 ss.272A-274C.",
)
def strategy_property_income_finance_cost(facts: dict, tax_year: str) -> dict:
    rental_income = max(0.0, float(facts.get("rental_income", 0)))
    allowable_expenses = max(0.0, float(facts.get("allowable_expenses", 0)))
    finance_costs = max(0.0, float(facts.get("finance_costs", 0)))
    other_income = max(0.0, float(facts.get("other_income", 0)))

    rental_profit = max(0.0, rental_income - allowable_expenses)
    reducer_rate = get_parameter(
        "property_income.finance_cost_restriction", tax_year
    )["reducer_rate"]
    personal_allowance = get_parameter("income_tax.personal_allowance", tax_year)["amount"]

    total_income = other_income + rental_profit
    adjusted_total_income = max(0.0, total_income - personal_allowance)
    restricted = min(finance_costs, rental_profit, adjusted_total_income)
    tax_reducer = round(restricted * reducer_rate, 2)
    finance_costs_carried_forward = round(finance_costs - restricted, 2)

    tax_before_reducer = income_tax_on_earned_income(
        {"total_income": total_income}, tax_year
    )["tax_due"]
    tax_under_s24 = round(tax_before_reducer - tax_reducer, 2)

    tax_if_deductible = income_tax_on_earned_income(
        {"total_income": max(0.0, total_income - finance_costs)}, tax_year
    )["tax_due"]

    return {
        "rental_profit": round(rental_profit, 2),
        "finance_costs": round(finance_costs, 2),
        "basic_rate_tax_reducer": tax_reducer,
        "finance_costs_carried_forward": finance_costs_carried_forward,
        "tax_under_s24": tax_under_s24,
        "tax_if_interest_fully_deductible": tax_if_deductible,
        "extra_tax_from_restriction": round(tax_under_s24 - tax_if_deductible, 2),
    }


@register(
    "strategy.partnership_profit_allocation",
    consumes=[
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "national_insurance.class4",
    ],
    description="Partnership/LLP profit-share planning: a partnership is tax-transparent, so each "
    "partner is taxed on their share of the profit as trading income (income tax + Class 4 NIC) on "
    "top of their other income. Where two partners are in different tax bands, the profit-sharing "
    "ratio drives the combined tax. This compares the current allocation with a proposed one and "
    "quantifies the difference. The ratio must reflect the partners' genuine commercial "
    "contribution — it cannot be set for tax alone — a judgement the adviser confirms.",
)
def strategy_partnership_profit_allocation(facts: dict, tax_year: str) -> dict:
    total_profit = max(0.0, float(facts.get("total_profit", 0)))
    p1_other = max(0.0, float(facts.get("partner1_other_income", 0)))
    p2_other = max(0.0, float(facts.get("partner2_other_income", 0)))
    current_p1 = min(1.0, max(0.0, float(facts.get("current_partner1_share", 0.5))))
    proposed_p1 = min(1.0, max(0.0, float(facts.get("proposed_partner1_share", current_p1))))

    def _partner_tax(share_profit: float, other_income: float) -> float:
        income_tax = combined_personal_tax(
            {"earned_income": other_income + share_profit, "dividend_income": 0}, tax_year
        )["total_tax"]
        return round(income_tax + _class4_nic(share_profit, tax_year), 2)

    # N-partner mode: an explicit list of partners, each taxed on their share
    # plus their other income. Used for firms with more than two partners.
    partners_input = facts.get("partners")
    if partners_input:
        partner_results = []
        total_tax = 0.0
        for i, p in enumerate(partners_input, 1):
            share_profit = round(total_profit * float(p.get("profit_share", 0)), 2)
            other = max(0.0, float(p.get("other_income", 0)))
            tax = _partner_tax(share_profit, other)
            partner_results.append(
                {"partner": i, "profit_share": share_profit, "tax": tax}
            )
            total_tax += tax
        return {
            "total_profit": round(total_profit, 2),
            "number_of_partners": len(partner_results),
            "partners": partner_results,
            "total_tax": round(total_tax, 2),
        }

    def _allocation(p1_share: float) -> dict:
        p1_profit = round(total_profit * p1_share, 2)
        p2_profit = round(total_profit - p1_profit, 2)
        t1 = _partner_tax(p1_profit, p1_other)
        t2 = _partner_tax(p2_profit, p2_other)
        return {
            "partner1_profit": p1_profit, "partner2_profit": p2_profit,
            "partner1_tax": t1, "partner2_tax": t2, "total_tax": round(t1 + t2, 2),
        }

    current = _allocation(current_p1)
    proposed = _allocation(proposed_p1)
    return {
        "total_profit": round(total_profit, 2),
        "current_total_tax": current["total_tax"],
        "proposed_total_tax": proposed["total_tax"],
        "tax_saving": round(current["total_tax"] - proposed["total_tax"], 2),
        "current": current,
        "proposed": proposed,
    }


# Statutory structure of the relevant-property regime (IHTA 1984 ss.64-69),
# fixed by the Act rather than annually re-rated: the ten-year charge is 30%
# of lifetime rates, and the exit charge is proportioned over the 40 quarters
# of a ten-year cycle. The rate that varies (the 20% lifetime rate) and the
# nil-rate band come from the rate store.
_TEN_YEAR_CHARGE_FACTOR = 0.30
_QUARTERS_PER_CYCLE = 40


@register(
    "strategy.relevant_property_trust_charges",
    consumes=["iht.rates", "iht.nil_rate_band"],
    description="Relevant-property trust IHT charges (discretionary and most lifetime trusts, "
    "IHTA 1984 ss.58-69): the 20% entry charge on value settled above the available nil-rate "
    "band; the ten-year anniversary (principal) charge of up to 6% of the value above the band "
    "(30% of lifetime rates); and the proportionate exit charge when property leaves between "
    "anniversaries, based on the last ten-year effective rate and the complete quarters elapsed. "
    "Quantifies all three so a settlor can weigh a trust against outright gifts.",
)
def strategy_relevant_property_trust_charges(facts: dict, tax_year: str) -> dict:
    nrb = get_parameter("iht.nil_rate_band", tax_year)["amount"]
    lifetime_rate = get_parameter("iht.rates", tax_year)["lifetime_clt_rate"]
    # Related settlements made on the same day share one nil-rate band, so
    # their value reduces the band available to this trust (IHTA 1984 s.62;
    # anti-Rysaffe multiple-trust rule). Additive: defaults to no reduction.
    related_settlements = max(0.0, float(facts.get("same_day_settlements_value", 0)))
    available_nrb = max(0.0, float(facts.get("available_nrb", nrb)) - related_settlements)

    amount_settled = max(0.0, float(facts.get("amount_settled", 0)))
    trust_value = max(0.0, float(facts.get("trust_value", 0)))
    amount_distributed = max(0.0, float(facts.get("amount_distributed", 0)))
    quarters = max(0, min(_QUARTERS_PER_CYCLE, int(facts.get("quarters_since_last_charge", 0))))

    entry_charge = round(lifetime_rate * max(0.0, amount_settled - available_nrb), 2)

    ten_year_charge = round(
        _TEN_YEAR_CHARGE_FACTOR * lifetime_rate * max(0.0, trust_value - available_nrb), 2
    )
    ten_year_effective_rate = round(ten_year_charge / trust_value, 6) if trust_value else 0.0

    exit_charge = round(
        ten_year_effective_rate * (quarters / _QUARTERS_PER_CYCLE) * amount_distributed, 2
    )

    return {
        "available_nrb": round(available_nrb, 2),
        "entry_charge": entry_charge,
        "ten_year_charge": ten_year_charge,
        "ten_year_effective_rate": ten_year_effective_rate,
        "exit_charge": exit_charge,
    }


def _transfer_land_tax(price: float, jurisdiction: str, tax_year: str) -> float:
    """Land tax on the market-value transfer into the company, at the
    additional-dwelling rate, for the right UK nation."""
    facts = {"price": price, "additional_dwelling": True}
    if jurisdiction == "scotland":
        return lbtt_residential(facts, tax_year)["total_lbtt"]
    if jurisdiction == "wales":
        return ltt_residential(facts, tax_year)["total_ltt"]
    return sdlt_residential(facts, tax_year)["total_sdlt"]


@register(
    "strategy.property_incorporation",
    consumes=[
        "sdlt.residential_bands",
        "lbtt.residential_bands",
        "ltt.residential_bands",
        "corporation_tax.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
        "property_income.finance_cost_restriction",
        "cgt.rates",
    ],
    description="The property-incorporation decision: should a landlord move their portfolio into "
    "a company? Compares the ongoing personal tax on the rental business under the s.24 interest "
    "restriction against the corporation tax a company pays (interest fully deductible, profits "
    "retained), then weighs that annual saving against the one-off cost of incorporating — the "
    "SDLT on transferring the properties at market value (with the 5% additional-dwelling "
    "surcharge) plus any CGT, which is deferred where s.162 incorporation relief applies. Reports "
    "the break-even in years. The land tax on transfer follows the property's UK nation "
    "(SDLT/LBTT/LTT); the headline saving assumes profits are retained, and a separate "
    "after-extraction figure shows the position once the post-tax profit is drawn as dividends. "
    "The accountant confirms the s.162 'business' test and any ATED (usually relieved for a "
    "commercial letting business).",
)
def strategy_property_incorporation(facts: dict, tax_year: str) -> dict:
    portfolio_value = max(0.0, float(facts.get("portfolio_value", 0)))
    rental_profit = max(0.0, float(facts.get("rental_profit", 0)))
    finance_costs = max(0.0, float(facts.get("finance_costs", 0)))
    other_income = max(0.0, float(facts.get("other_income", 0)))
    latent_gain = max(0.0, float(facts.get("latent_gain", 0)))
    s162_relief = bool(facts.get("s162_relief_available", False))

    # Personal ongoing tax on the rental business, under the s.24 restriction:
    # the incremental income tax on the rental profit, less the 20% reducer.
    personal_allowance = get_parameter("income_tax.personal_allowance", tax_year)["amount"]
    reducer_rate = get_parameter(
        "property_income.finance_cost_restriction", tax_year
    )["reducer_rate"]
    it_with_rental = income_tax_on_earned_income(
        {"total_income": other_income + rental_profit}, tax_year
    )["tax_due"]
    it_other_only = income_tax_on_earned_income({"total_income": other_income}, tax_year)["tax_due"]
    adjusted_total_income = max(0.0, other_income + rental_profit - personal_allowance)
    reducer = round(min(finance_costs, rental_profit, adjusted_total_income) * reducer_rate, 2)
    personal_annual_tax = round((it_with_rental - it_other_only) - reducer, 2)

    # Company ongoing tax: interest fully deductible, profits retained.
    company_profit = max(0.0, rental_profit - finance_costs)
    company_annual_tax = corporation_tax({"taxable_profit": company_profit}, tax_year)["tax_due"]

    annual_saving = round(personal_annual_tax - company_annual_tax, 2)

    # One-off cost of incorporating: the land tax on the deemed market-value
    # transfer (companies pay the additional-dwelling rate) — SDLT (England/NI),
    # LBTT (Scotland) or LTT (Wales) — plus CGT unless s.162 incorporation relief
    # defers the gain into the shares.
    jurisdiction = str(facts.get("jurisdiction", "england")).lower()
    land_tax_on_transfer = _transfer_land_tax(portfolio_value, jurisdiction, tax_year)
    cgt_rate = get_parameter("cgt.rates", tax_year)["residential"]["higher"]
    cgt_on_transfer = 0.0 if s162_relief else round(latent_gain * cgt_rate, 2)
    one_off_cost = round(land_tax_on_transfer + cgt_on_transfer, 2)

    break_even_years = round(one_off_cost / annual_saving, 2) if annual_saving > 0 else None

    # Extraction: drawing the company's post-CT profit out as dividends adds
    # dividend tax, so the retained-profits saving overstates the benefit for a
    # landlord who actually wants the income now.
    post_ct_profit = round(max(0.0, company_profit - company_annual_tax), 2)
    extract = bool(facts.get("extract_profits", False))
    if extract and post_ct_profit > 0:
        # Incremental dividend tax on drawing the post-CT profit, composed
        # through combined_personal_tax so the personal allowance and band
        # interaction with the owner's other income is handled correctly.
        without_div = combined_personal_tax(
            {"earned_income": other_income, "dividend_income": 0}, tax_year
        )["total_tax"]
        with_div = combined_personal_tax(
            {"earned_income": other_income, "dividend_income": post_ct_profit}, tax_year
        )["total_tax"]
        dividend_tax_on_extraction = round(with_div - without_div, 2)
    else:
        dividend_tax_on_extraction = 0.0
    company_total_tax_if_extracted = round(company_annual_tax + dividend_tax_on_extraction, 2)
    annual_saving_after_extraction = round(
        personal_annual_tax - company_total_tax_if_extracted, 2
    )

    return {
        "personal_annual_tax": personal_annual_tax,
        "company_annual_tax": company_annual_tax,
        "annual_tax_saving": annual_saving,
        # sdlt_on_transfer kept as the England figure for back-compat; use
        # land_tax_on_transfer for the jurisdiction-correct charge.
        "sdlt_on_transfer": land_tax_on_transfer,
        "land_tax_on_transfer": land_tax_on_transfer,
        "cgt_on_transfer": cgt_on_transfer,
        "one_off_cost": one_off_cost,
        "break_even_years": break_even_years,
        "dividend_tax_on_extraction": dividend_tax_on_extraction,
        "company_total_tax_if_extracted": company_total_tax_if_extracted,
        "annual_saving_after_extraction": annual_saving_after_extraction,
    }


@register(
    "strategy.venture_capital_investment",
    consumes=["venture_capital.schemes", "cgt.rates"],
    description="EIS / SEIS / VCT investment relief: income tax relief at the scheme rate on the "
    "investment (up to the annual limit and capped at the investor's income tax liability), plus "
    "the scheme's CGT treatment — EIS defers a reinvested gain, SEIS exempts 50% of it, VCT pays "
    "tax-free dividends. Quantifies the income tax relief, the CGT deferred or saved, and the net "
    "cost after relief (ITA 2007 Parts 5, 5A, 6). Whether the company and shares qualify is a "
    "judgement the adviser confirms; relief is withdrawn if the minimum holding period is not met.",
)
def strategy_venture_capital_investment(facts: dict, tax_year: str) -> dict:
    scheme = str(facts.get("scheme", "eis")).lower()
    schemes = get_parameter("venture_capital.schemes", tax_year)
    if scheme not in schemes:
        raise ValueError(f"Unknown venture-capital scheme: {scheme!r}")
    s = schemes[scheme]

    amount = max(0.0, float(facts.get("amount_invested", 0)))
    it_liability = max(0.0, float(facts.get("income_tax_liability", 0)))
    gain_reinvested = max(0.0, float(facts.get("gain_reinvested", 0)))
    is_higher = bool(facts.get("is_higher_rate", True))

    eligible = min(amount, s["annual_limit"])
    relief_rate = s["relief_rate"]
    uncapped_relief = round(eligible * relief_rate, 2)
    income_tax_relief = round(min(uncapped_relief, it_liability), 2)
    capped = income_tax_relief < uncapped_relief

    cgt_rate = get_parameter("cgt.rates", tax_year)["other"][
        "higher" if is_higher else "lower"
    ]

    cgt_deferred = 0.0
    cgt_permanently_saved = 0.0
    if s["cgt_deferral"]:
        cgt_deferred = round(min(gain_reinvested, eligible) * cgt_rate, 2)
    if s["cgt_reinvestment_relief_rate"] > 0:
        exempt_gain = min(gain_reinvested, eligible) * s["cgt_reinvestment_relief_rate"]
        cgt_permanently_saved = round(exempt_gain * cgt_rate, 2)

    net_cost = round(eligible - income_tax_relief - cgt_permanently_saved, 2)

    return {
        "scheme": scheme,
        "eligible_investment": round(eligible, 2),
        "income_tax_relief_rate": relief_rate,
        "income_tax_relief": income_tax_relief,
        "capped_by_income_tax_liability": capped,
        "cgt_deferred": cgt_deferred,
        "cgt_permanently_saved": cgt_permanently_saved,
        "tax_free_dividends": bool(s["tax_free_dividends"]),
        "net_cost_after_relief": net_cost,
    }


@register(
    "strategy.rd_tax_relief",
    consumes=["rd.merged_scheme", "corporation_tax.rates"],
    description="R&D tax relief under the merged scheme (accounting periods from 1 April 2024): a "
    "20% taxable expenditure credit (RDEC) on qualifying R&D spend. Because the credit is itself "
    "chargeable to corporation tax, the net benefit is 20% less tax at the company's rate. "
    "Quantifies the gross credit, the tax on it and the net cash benefit (CTA 2009 Part 13). "
    "Loss-making R&D-intensive SMEs use a different rate — flagged for the adviser.",
)
def strategy_rd_tax_relief(facts: dict, tax_year: str) -> dict:
    spend = max(0.0, float(facts.get("qualifying_rd_spend", 0)))
    rdec_rate = get_parameter("rd.merged_scheme", tax_year)["rdec_rate"]
    ct = get_parameter("corporation_tax.rates", tax_year)
    marginal = float(facts.get("marginal_rate", ct["main_rate"]))

    gross_credit = round(spend * rdec_rate, 2)
    tax_on_credit = round(gross_credit * marginal, 2)
    net_benefit = round(gross_credit - tax_on_credit, 2)
    return {
        "qualifying_rd_spend": round(spend, 2),
        "rdec_rate": rdec_rate,
        "gross_credit": gross_credit,
        "tax_on_credit": tax_on_credit,
        "net_benefit": net_benefit,
    }


@register(
    "strategy.patent_box",
    consumes=["patent_box.rate", "corporation_tax.rates"],
    description="Patent Box: profits attributable to patented inventions can be taxed at an "
    "effective 10% corporation-tax rate instead of the main rate. Quantifies the tax at the main "
    "rate, the tax under the Patent Box and the saving (CTA 2010 Part 8A). The apportionment of "
    "profit to qualifying IP and the modified-nexus R&D fraction are the adviser's to establish.",
)
def strategy_patent_box(facts: dict, tax_year: str) -> dict:
    patent_profit = max(0.0, float(facts.get("patent_profit", 0)))
    pb_rate = get_parameter("patent_box.rate", tax_year)["rate"]
    ct = get_parameter("corporation_tax.rates", tax_year)
    marginal = float(facts.get("marginal_rate", ct["main_rate"]))

    tax_at_main_rate = round(patent_profit * marginal, 2)
    tax_under_patent_box = round(patent_profit * pb_rate, 2)
    return {
        "patent_profit": round(patent_profit, 2),
        "patent_box_rate": pb_rate,
        "tax_at_main_rate": tax_at_main_rate,
        "tax_under_patent_box": tax_under_patent_box,
        "tax_saving": round(tax_at_main_rate - tax_under_patent_box, 2),
    }


@register(
    "strategy.commercial_property_fixtures",
    consumes=["capital_allowances.aia", "corporation_tax.rates"],
    description="Capital allowances on integral features and fixtures within a commercial "
    "building (heating, electrics, lifts, etc.): the identified fixtures value attracts plant and "
    "machinery allowances — 100% via the Annual Investment Allowance up to its limit, then the "
    "special-rate writing-down allowance on any excess. Quantifies the first-year allowance and "
    "the tax it saves at the company's marginal rate (CAA 2001 ss.33A/187A). On a second-hand "
    "building the s.187A pooling/fixed-value conditions must be met — the adviser confirms.",
)
def strategy_commercial_property_fixtures(facts: dict, tax_year: str) -> dict:
    fixtures_value = max(0.0, float(facts.get("fixtures_value", 0)))
    aia = get_parameter("capital_allowances.aia", tax_year)
    aia_limit, special_wda = aia["aia_limit"], aia["special_rate_wda"]
    ct = get_parameter("corporation_tax.rates", tax_year)
    marginal = float(facts.get("marginal_rate", ct["main_rate"]))

    aia_used = min(fixtures_value, aia_limit)
    excess = max(0.0, fixtures_value - aia_limit)
    written_down_first_year = round(excess * special_wda, 2)
    first_year_allowance = round(aia_used + written_down_first_year, 2)
    return {
        "fixtures_value": round(fixtures_value, 2),
        "aia_used": round(aia_used, 2),
        "written_down_first_year": written_down_first_year,
        "first_year_allowance": first_year_allowance,
        "tax_saved_year_one": round(first_year_allowance * marginal, 2),
    }


@register(
    "strategy.eot_disposal_relief",
    consumes=["cgt.business_asset_disposal_relief", "cgt.rates"],
    description="Employee Ownership Trust sale: an owner who sells a controlling interest in a "
    "trading company to an EOT pays no capital gains tax on the disposal (a full exemption), "
    "against the CGT a normal third-party sale would bear (Business Asset Disposal Relief at 14% "
    "on the first £1m, then the standard share rate). Quantifies the CGT saved. The qualifying "
    "conditions — tightened by Finance Act 2024/2025 (UK-resident trustees, no retained control, "
    "clawback period, independent valuation) — are the adviser's to confirm (TCGA 1992 s.236H).",
)
def strategy_eot_disposal_relief(facts: dict, tax_year: str) -> dict:
    gain = max(0.0, float(facts.get("disposal_gain", 0)))
    badr_available = bool(facts.get("badr_available", True))
    badr_used = max(0.0, float(facts.get("badr_lifetime_used", 0)))

    badr = get_parameter("cgt.business_asset_disposal_relief", tax_year)
    badr_rate, lifetime_limit = badr["rate"], badr["lifetime_limit"]
    higher_rate = get_parameter("cgt.rates", tax_year)["other"]["higher"]

    badr_amount = min(gain, max(0.0, lifetime_limit - badr_used)) if badr_available else 0.0
    excess = gain - badr_amount
    cgt_without_eot = round(badr_amount * badr_rate + excess * higher_rate, 2)
    return {
        "disposal_gain": round(gain, 2),
        "cgt_without_eot": cgt_without_eot,
        "cgt_under_eot": 0.0,
        "cgt_saved": cgt_without_eot,
    }


@register(
    "strategy.pension_death_benefit",
    consumes=["iht.rates", "iht.nil_rate_band"],
    description="Pension death-benefit IHT (announced Autumn Budget 2024): from 6 April 2027 most "
    "unused pension funds are expected to fall within the estate for inheritance tax, where today "
    "they normally pass outside it. Quantifies the extra IHT a pension pot would attract from that "
    "date (40% where the estate is already above the nil-rate band). This is a forward-looking "
    "projection subject to final legislation — flagged borderline; the plan is to review as the "
    "Finance Bill 2025-26 is enacted (amending IHTA 1984).",
)
def strategy_pension_death_benefit(facts: dict, tax_year: str) -> dict:
    pot = max(0.0, float(facts.get("pension_pot_value", 0)))
    estate_above_nrb = bool(facts.get("estate_above_nrb", True))
    death_rate = get_parameter("iht.rates", tax_year)["death_rate"]

    iht_from_2027 = round(pot * death_rate, 2) if estate_above_nrb else 0.0
    return {
        "pension_pot_value": round(pot, 2),
        "iht_before_april_2027": 0.0,
        "iht_from_april_2027": iht_from_2027,
        "extra_iht_from_reform": iht_from_2027,
    }


@register(
    "strategy.life_policy_in_trust",
    consumes=["iht.rates"],
    description="Writing a life policy in trust: the sum assured is paid to the trust on death, "
    "outside the estate, providing tax-free funds to meet the inheritance tax bill. If instead the "
    "policy were held personally, the proceeds would add to the estate and attract 40% IHT. "
    "Quantifies the IHT saved by writing it in trust and confirms the payout available to cover "
    "the bill (IHTA 1984 s.5). The policy must be validly settled with no reservation of benefit.",
)
def strategy_life_policy_in_trust(facts: dict, tax_year: str) -> dict:
    sum_assured = max(0.0, float(facts.get("sum_assured", 0)))
    estate_above_nrb = bool(facts.get("estate_above_nrb", True))
    death_rate = get_parameter("iht.rates", tax_year)["death_rate"]

    iht_if_held_personally = round(sum_assured * death_rate, 2) if estate_above_nrb else 0.0
    return {
        "sum_assured": round(sum_assured, 2),
        "iht_if_held_personally": iht_if_held_personally,
        "iht_if_written_in_trust": 0.0,
        "iht_saved_by_writing_in_trust": iht_if_held_personally,
        "payout_available_for_iht_bill": round(sum_assured, 2),
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
    "strategy.cgt_timing_of_disposals",
    consumes=[
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.personal_allowance",
        "income_tax.bands",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Splitting a divisible holding's disposal across two tax years so two annual "
    "exempt amounts (and two basic-rate bands) are used instead of one (TCGA 1992 ss.1H-1K). "
    "Only applies to divisible assets such as shares/units — a single property cannot be "
    "part-sold across years. The second year is modelled at the same rates and income "
    "position (a documented planning assumption).",
)
def strategy_cgt_timing_of_disposals(facts: dict, tax_year: str) -> dict:
    gain = max(0.0, float(facts["disposal_gain"]))
    asset_type = facts.get("asset_type", "other")
    earned_income = float(facts.get("earned_income", 0))
    dividend_income = float(facts.get("dividend_income", 0))

    common = {
        "asset_type": asset_type,
        "earned_income": earned_income,
        "dividend_income": dividend_income,
    }
    whole = cgt_liability({**common, "chargeable_gain": gain}, tax_year)
    first_half = round(gain / 2, 2)
    leg1 = cgt_liability({**common, "chargeable_gain": first_half}, tax_year)
    leg2 = cgt_liability({**common, "chargeable_gain": round(gain - first_half, 2)}, tax_year)
    split_total = round(leg1["tax_due"] + leg2["tax_due"], 2)

    return {
        "disposal_gain": gain,
        "cgt_if_sold_in_one_year": whole["tax_due"],
        "cgt_if_split_over_two_years": split_total,
        "saving_from_splitting": round(whole["tax_due"] - split_total, 2),
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
    "strategy.cgt_rollover_relief",
    consumes=[
        "cgt.annual_exempt_amount",
        "cgt.rates",
        "income_tax.bands",
        "income_tax.personal_allowance",
        "dividend_tax.allowance",
        "dividend_tax.bands",
    ],
    description="Business-asset rollover relief (TCGA 1992 s.152): the gain on a qualifying "
    "business asset is rolled into the base cost of replacement assets acquired between 12 "
    "months before and 3 years after the disposal, deferring the CGT. Partial reinvestment "
    "leaves the smaller of the gain and the proceeds not reinvested chargeable now. Both "
    "assets must be s.155 classes used only for the trade — conditions the adviser confirms.",
)
def strategy_cgt_rollover_relief(facts: dict, tax_year: str) -> dict:
    proceeds = max(0.0, float(facts.get("disposal_proceeds", 0)))
    gain = max(0.0, float(facts.get("disposal_gain", 0)))
    replacement_cost = max(0.0, float(facts.get("replacement_cost", 0)))
    asset_type = facts.get("asset_type", "other")
    earned_income = max(0.0, float(facts.get("earned_income", 0)))
    dividend_income = max(0.0, float(facts.get("dividend_income", 0)))

    # s.152/s.153: full reinvestment of the proceeds defers the whole gain;
    # otherwise the amount not reinvested is chargeable now, capped at the gain.
    amount_not_reinvested = max(0.0, round(proceeds - replacement_cost, 2))
    chargeable_now = round(min(gain, amount_not_reinvested), 2)
    rolled_over = round(gain - chargeable_now, 2)

    common = {
        "asset_type": asset_type,
        "earned_income": earned_income,
        "dividend_income": dividend_income,
    }
    without_relief = cgt_liability({**common, "chargeable_gain": gain}, tax_year)
    with_relief = cgt_liability({**common, "chargeable_gain": chargeable_now}, tax_year)

    return {
        "disposal_proceeds": round(proceeds, 2),
        "disposal_gain": round(gain, 2),
        "replacement_cost": round(replacement_cost, 2),
        "amount_not_reinvested": amount_not_reinvested,
        "gain_chargeable_now": chargeable_now,
        "gain_rolled_over": rolled_over,
        "cgt_without_relief": without_relief["tax_due"],
        "cgt_with_relief": with_relief["tax_due"],
        "tax_deferred": round(without_relief["tax_due"] - with_relief["tax_due"], 2),
        # The rolled-over gain reduces the replacement asset's base cost, so
        # it comes back into charge on a future disposal of the new asset.
        "replacement_base_cost_reduction": rolled_over,
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
