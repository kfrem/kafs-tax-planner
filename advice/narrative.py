"""Client-facing narrative drafting under the architecture doc §8
guardrails, which are enforced here in code, not policy:

1. The engine's computed payload is the ONLY source of numbers,
   strategies, and citations.
2. Every draft — whoever wrote it — passes through ``validate_narrative``
   before it can be stored. A draft containing any number or citation
   not present in the advice record is rejected outright.
3. The default drafter is DETERMINISTIC (template composition from the
   payload): zero API cost, reproducible, and sufficient for MVP. An LLM
   drafter can be plugged in later (``draft_fn`` argument) and gets no
   special treatment: same validator, same rejection rules. An LLM is
   never the source of a number, citation, or risk classification.
"""

from __future__ import annotations

import re

RISK_SENTENCES = {
    "borderline": (
        "This position is BORDERLINE: it is lawful but attracts HMRC scrutiny, "
        "and you should weigh the disclosed risks with us before acting."
    ),
    "contested": (
        "This position is CONTESTED: HMRC actively challenges arrangements of "
        "this type and the outcome may depend on litigation."
    ),
    "untested": (
        "This position is UNTESTED: it has not been examined by a court or "
        "tribunal, and that uncertainty is part of the decision."
    ),
}

_HEADLINE_SENTENCES = {
    "salary-dividend-mix": lambda q: (
        f"Taking a salary of £{q['recommended']['salary']:,.0f} with the balance as dividends "
        f"leaves you £{q['recommended']['net_to_individual']:,.2f} after all taxes."
        if q.get("recommended") else ""
    ),
    "pension-annual-allowance-carry-forward": lambda q: (
        f"Of your intended pension contribution of £{q['desired_contribution']:,.0f}, "
        f"£{q['personal_route']['relievable_gross']:,.0f} attracts relief personally"
        + (
            f", and £{q['personal_route']['unrelieved_amount']:,.0f} would receive no relief — "
            f"a company contribution instead would save £{q['employer_route']['corporation_tax_saving']:,.2f} "
            "of corporation tax."
            if q["personal_route"]["unrelieved_amount"] > 0 and q.get("employer_route")
            else "."
        )
    ),
    "incorporation-vs-sole-trade": lambda q: (
        f"On profits of £{q['annual_profit']:,.0f}, our comparison supports "
        f"{'incorporating' if q['recommendation'] == 'incorporate' else 'remaining a sole trader'} at present."
    ),
    "marriage-allowance-transfer": lambda q: (
        f"A Marriage Allowance transfer would save £{q['estimated_annual_tax_saving']:,.2f} each year."
        if q.get("eligible") else ""
    ),
    "iht-spousal-transfer-and-nil-rate-bands": lambda q: (
        f"Structured wills with the transferable allowances claimed would leave inheritance tax of "
        f"£{q['second_death_with_transferred_bands']['tax_due']:,.2f} on the second death, against "
        f"£{q['second_death_without_claims']['tax_due']:,.2f} without the claims — the claims are worth "
        f"£{q['value_of_transferable_bands']:,.2f}."
    ),
    "iht-lifetime-gifting-pets": lambda q: (
        f"The planned gift of £{q['planned_gift']:,.0f} would save £{q['saving_if_survive_7_years']:,.2f} "
        "of inheritance tax if you survive it by seven years."
    ),
    "iht-charitable-legacy-reduced-rate": lambda q: (
        f"A charitable legacy of £{q['target_legacy_for_reduced_rate']:,.2f} would reduce the estate rate "
        f"to 36%, so its true cost to your family is £{q['net_cost_to_beneficiaries']:,.2f}."
        if not q.get("already_qualifies") and q.get("net_cost_to_beneficiaries") is not None else ""
    ),
    "cgt-ppr-relief": lambda q: (
        f"Private residence relief exempts £{q['exempt_gain']:,.2f} of the gain, leaving capital gains tax "
        f"of £{q['cgt_with_relief']:,.2f} — a saving of £{q['relief_saving']:,.2f}."
    ),
    "cgt-spousal-transfer-before-disposal": lambda q: (
        f"Transferring a half share to your spouse before sale would save £{q['saving']:,.2f} "
        "of capital gains tax."
    ),
    "sdlt-purchase-planning": lambda q: (
        f"Stamp duty on the planned purchase is £{q['as_planned']['total_sdlt']:,.2f}."
    ),
    "income-timing-across-years": lambda q: (
        f"Timing the £{q['shiftable_amount']:,.0f} to land in the "
        f"{'current' if q['recommendation'] == 'take_this_year' else 'following'} tax year "
        f"would save £{q['saving']:,.2f}."
        if q.get("recommendation") in ("take_this_year", "defer_to_next_year") else ""
    ),
    "payroll-giving": lambda q: (
        f"Giving £{q['annual_donation']:,.2f} through payroll costs you "
        f"£{q['net_cost_to_donor']:,.2f} after £{q['income_tax_saved']:,.2f} of tax relief, "
        f"and the charity receives the full amount."
        if q.get("annual_donation") else ""
    ),
    "charity-gift-of-assets": lambda q: (
        f"Gifting the asset worth £{q['gift_value']:,.0f} to charity would save "
        f"£{q['income_tax_saved']:,.2f} of income tax and £{q['cgt_avoided']:,.2f} of "
        f"capital gains tax — a combined benefit of £{q['total_tax_benefit']:,.2f}."
    ),
    "cgt-rollover-relief": lambda q: (
        f"Rolling the gain into the replacement assets defers "
        f"£{q['tax_deferred']:,.2f} of capital gains tax, leaving "
        f"£{q['cgt_with_relief']:,.2f} payable now."
    ),
    "capital-allowances-full-expensing": lambda q: (
        f"Full expensing relieves the whole £{q['new_main_rate_spend']:,.0f} of new plant "
        f"in year one, saving £{q['tax_saved_year_one']:,.2f} of corporation tax"
        + (
            f" — £{q['extra_tax_saved_year_one']:,.2f} more than the standard allowances route."
            if q.get("extra_tax_saved_year_one") else "."
        )
    ),
    "holding-company-structuring": lambda q: (
        f"Retaining £{q['amount_retained_in_group']:,.0f} in the group rather than "
        f"extracting it now defers £{q['tax_deferred_by_retention']:,.2f} of personal "
        f"dividend tax; the intercompany dividend itself is tax-free."
    ),
    "sdlt-mixed-use-classification": lambda q: (
        f"If the mixed-use classification holds, stamp duty falls to "
        f"£{q['mixed_use_sdlt']:,.2f} — a difference of £{q['saving_if_mixed_use']:,.2f} "
        f"against the residential treatment."
    ),
    "sdlt-uninhabitable-classification": lambda q: (
        f"If the property is genuinely not suitable for use as a dwelling, stamp duty "
        f"falls to £{q['non_residential_sdlt']:,.2f} — a difference of "
        f"£{q['saving_if_non_residential']:,.2f} against the residential treatment."
    ),
    "fhl-abolition-transition": lambda q: (
        f"With the holiday-let regime abolished, the finance-cost restriction now costs "
        f"£{q['extra_income_tax_from_s24']:,.2f} more income tax a year than the property "
        f"attracted as a furnished holiday let."
    ),
}


def deterministic_draft(record) -> str:
    """Compose the narrative purely from the record's own content: the
    tax editor's stored explanations plus headline figures."""
    paragraphs = [
        f"Dear {record.client.name},",
        f"Following our review of your affairs for {record.tax_year}, we set out below "
        "the planning opportunities our analysis identified. Figures are computed from "
        "the information you provided and current law; nothing here is to be acted on "
        "until we have discussed it together.",
    ]
    for result in record.results:
        sentence_builder = _HEADLINE_SENTENCES.get(result["strategy_code"])
        headline = sentence_builder(result["quantification"]) if sentence_builder else ""
        if not headline:
            continue
        block = f"{result['strategy_name']}. {headline}"
        risk_sentence = RISK_SENTENCES.get(result["risk_status"])
        if risk_sentence:
            block += " " + risk_sentence
        paragraphs.append(block)
    paragraphs.append(
        "The statutory basis for each recommendation is set out in the attached report, "
        "and each remains subject to our professional review before any step is taken."
    )
    return "\n\n".join(paragraphs)


# --- The validator (the §8 guardrail) -----------------------------------------

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numeric_leaves(value, out):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _numeric_leaves(item, out)
    elif isinstance(value, list):
        for item in value:
            _numeric_leaves(item, out)


def _allowed_number_strings(record) -> set[str]:
    """Every number the record itself contains, in the string forms prose
    uses: raw, 2dp, comma-grouped, and x100 for sub-1 rates."""
    numbers: set[float] = set()
    for result in record.results:
        _numeric_leaves(result["quantification"], numbers)
    expanded = set()
    for value in numbers:
        candidates = {value}
        if abs(value) <= 1:
            candidates.add(round(value * 100, 4))  # 0.36 -> "36%"
        for candidate in candidates:
            expanded.add(f"{candidate:g}")
            expanded.add(f"{candidate:,.2f}")
            expanded.add(f"{candidate:,.0f}")
            expanded.add(f"{candidate:.2f}")
            expanded.add(f"{candidate:.0f}")
    return expanded


def _record_text_blob(record) -> str:
    """The record's own prose: explanations, names, citations, tax year —
    numbers appearing there (statute years, '£3,000', '7 years') are
    legitimate source material for a narrative."""
    parts = [record.tax_year, record.tax_year.replace("/", " ")]
    for result in record.results:
        parts.extend([result["strategy_name"], result["explanation"]])
        parts.extend(a["citation"] for a in result["authorities"])
    return " ".join(parts)


def validate_narrative(text: str, record) -> dict:
    """Reject any draft containing a number or citation-like reference not
    present in the advice record. Returns {'valid': bool, 'violations': []}."""
    violations = []
    allowed_numbers = _allowed_number_strings(record)
    source_blob = _record_text_blob(record)

    for match in _NUMBER_RE.finditer(text):
        token = match.group(0)
        bare = token.replace(",", "")
        variants = {token, bare}
        try:
            value = float(bare)
            variants.update({f"{value:g}", f"{value:,.2f}", f"{value:.2f}", f"{value:,.0f}", f"{value:.0f}"})
        except ValueError:
            pass
        if variants & allowed_numbers:
            continue
        if token in source_blob or bare in source_blob:
            continue
        violations.append(f"Number '{token}' does not appear in the advice record.")

    for citation_match in re.finditer(r"\b(?:[A-Z][A-Za-z]*\s)+Act\s\d{4}|\[\d{4}\]\s?[A-Z]+\s?\d+", text):
        citation = citation_match.group(0)
        if citation not in source_blob:
            violations.append(f"Citation-like reference '{citation}' is not among the record's authorities.")

    return {"valid": not violations, "violations": violations}


class NarrativeRejected(Exception):
    pass


def create_narrative(record, user, draft_fn=deterministic_draft, drafter_name="deterministic-v1"):
    """Draft -> validate -> store. Storage is impossible for a draft that
    fails validation, whatever produced it."""
    from .models import AdviceNarrative

    text = draft_fn(record)
    report = validate_narrative(text, record)
    if not report["valid"]:
        raise NarrativeRejected(
            "Narrative rejected by the validator: " + "; ".join(report["violations"])
        )
    narrative = AdviceNarrative(
        firm=record.firm,
        advice_record=record,
        text=text,
        drafter=drafter_name,
        validation_report=report,
        created_by=user,
    )
    narrative.save()
    return narrative
