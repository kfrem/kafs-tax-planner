"""Guided intake: the app must ASK the questions that change the answer rather
than silently assume them. Given a client's facts, ``intake_gaps`` returns the
material questions that are unanswered, why each matters, and the assumption the
engine would otherwise make — so the accountant confirms or corrects before
relying on the advice.

This is deterministic and data-driven (architecture doc §8 style): the same
facts always produce the same gaps, so the intake review is itself audit
evidence. It is the safety net behind fact-driven eligibility — a strategy can
only fire on the facts present, and this flags the facts whose *absence* is a
silent assumption.

Each check is (key, question, why, applies, answered, assumption):
* applies(facts)  — is this situation in play at all?
* answered(facts) — has the fact that removes the assumption been provided?
  (presence-based, because 0 / False are themselves valid answers)
"""

from __future__ import annotations


def _has(bucket: dict, key: str) -> bool:
    """The fact has been positively recorded (key present, not None)."""
    return key in bucket and bucket[key] is not None


CHECKS = [
    {
        "key": "marital_status",
        "question": "Is the client married or in a civil partnership, and if so what is the "
        "spouse's income?",
        "why": "A spouse can hold assets to use their own allowances and tax bands, enable a "
        "Marriage Allowance transfer, and take inter-spouse transfers of assets or gains with no "
        "CGT/IHT — several strategies depend on it.",
        "applies": lambda f: True,
        "answered": lambda f: _has(f.get("personal", {}), "spouse_income"),
        "assumption": "Assumed no spouse/civil partner: Marriage Allowance and inter-spouse "
        "CGT/IHT transfers were not considered.",
    },
    {
        "key": "property_jurisdiction",
        "question": "In which UK nation is the property located (England/NI, Scotland or Wales)?",
        "why": "Land tax differs by nation: SDLT (England/NI), LBTT (Scotland) and LTT (Wales) "
        "have different rates, bands and reliefs, so the figure changes materially.",
        "applies": lambda f: f.get("property", {}).get("purchase_price", 0) > 0
        or f.get("property", {}).get("lease_annual_rent", 0) > 0,
        "answered": lambda f: _has(f.get("property", {}), "jurisdiction"),
        "assumption": "Assumed the property is in England/NI (SDLT); Scotland (LBTT) and Wales "
        "(LTT) would give different figures.",
    },
    {
        "key": "landlord_mortgage",
        "question": "Is the let property mortgaged, and if so what is the annual interest?",
        "why": "Since April 2020 a residential landlord's mortgage interest is only relieved at "
        "20% (s.24), which materially raises a higher-rate landlord's tax.",
        "applies": lambda f: f.get("property", {}).get("rental_income", 0) > 0,
        "answered": lambda f: _has(f.get("property", {}), "finance_costs"),
        "assumption": "Assumed the let is unmortgaged: the s.24 finance-cost restriction was not "
        "applied.",
    },
    {
        "key": "bpr_qualification",
        "question": "Does the business/agricultural property qualify for relief — a trading (not "
        "investment) business, owned at least two years?",
        "why": "Business/Agricultural Property Relief only applies to qualifying assets; an "
        "investment business or a recent acquisition may not qualify at all.",
        "applies": lambda f: f.get("estate", {}).get("qualifying_business_property", 0) > 0,
        "answered": lambda f: _has(f.get("estate", {}), "bpr_qualification_confirmed"),
        "assumption": "Assumed the business/agricultural property qualifies for relief (trading, "
        "two-year ownership).",
    },
    {
        "key": "pension_taper",
        "question": "For a high earner, what are the client's threshold and adjusted income (to "
        "test the annual-allowance taper)?",
        "why": "Where adjusted income exceeds £260,000 the £60,000 annual allowance is tapered, "
        "so a large contribution can trigger an annual-allowance charge.",
        "applies": lambda f: f.get("pension", {}).get("desired_contribution", 0) > 0
        or f.get("personal", {}).get("desired_pension_contribution", 0) > 0,
        "answered": lambda f: _has(f.get("pension", {}), "adjusted_income"),
        "assumption": "Assumed no annual-allowance taper: for income over £200,000 the allowance "
        "may be reduced.",
    },
    {
        "key": "partnership_commercial",
        "question": "Does the proposed profit-sharing ratio reflect the partners' genuine "
        "commercial contribution?",
        "why": "A partnership profit share cannot be set purely to save tax; HMRC can challenge a "
        "tax-driven allocation under the settlements rules.",
        "applies": lambda f: f.get("partnership", {}).get("total_profit", 0) > 0,
        "answered": lambda f: _has(f.get("partnership", {}), "commercial_justification_confirmed"),
        "assumption": "Assumed the proposed profit share reflects genuine commercial "
        "contribution.",
    },
    {
        "key": "ated_on_incorporation",
        "question": "If the portfolio is incorporated, is any single dwelling worth over £500,000 "
        "and not let to a third party on commercial terms?",
        "why": "A company holding a dwelling over £500,000 pays the Annual Tax on Enveloped "
        "Dwellings unless a relief applies. A genuine commercial letting business is normally "
        "relieved, but an owner-occupied or connected-party dwelling is not — an annual cost that "
        "changes the incorporation decision.",
        "applies": lambda f: f.get("property", {}).get("portfolio_value", 0) > 0,
        "answered": lambda f: _has(f.get("property", {}), "ated_relief_confirmed"),
        "assumption": "Assumed ATED relief applies (a commercial letting business), so no ATED "
        "charge was included.",
    },
    {
        "key": "trust_prior_transfers",
        "question": "Has the settlor made any chargeable transfers in the seven years before "
        "creating the trust?",
        "why": "Prior chargeable transfers reduce the nil-rate band available to the trust, which "
        "increases the entry and ten-year charges.",
        "applies": lambda f: f.get("trust", {}).get("trust_value", 0) > 0
        or f.get("trust", {}).get("amount_settled", 0) > 0,
        "answered": lambda f: _has(f.get("trust", {}), "available_nrb"),
        "assumption": "Assumed a full nil-rate band is available to the trust; prior chargeable "
        "transfers would reduce it.",
    },
    # --- Checks derived from professional tax-examination material (see the Tax
    # Intelligence Brain milestone). Each surfaces a make-or-break fact that the
    # examiners' reports show is commonly missed. Pure issue-spotting: they flag
    # an assumption, they do not change any computed figure. ---
    {
        "key": "fixtures_s198_election",
        "question": "For fixtures within an acquired property, did the seller pool the fixtures "
        "and has a s.198 CAA 2001 election been signed by both parties?",
        "why": "Without the seller pooling the fixtures and a signed s.198 election, the buyer can "
        "claim NO capital allowances on those fixtures — the single fact that decides whether the "
        "relief exists at all.",
        "applies": lambda f: f.get("company", {}).get("fixtures_value", 0) > 0,
        "answered": lambda f: _has(f.get("company", {}), "fixtures_s198_confirmed"),
        "assumption": "Assumed the fixtures qualify for capital allowances; without seller pooling "
        "and a signed s.198 election no allowances are available on them.",
    },
    {
        "key": "venture_capital_connection",
        "question": "Is the investor connected with the EIS/SEIS company — an employee, a director "
        "outside the permitted limits, or holding more than 30% of the shares or voting rights?",
        "why": "Connection can deny EIS/SEIS income-tax relief, although CGT deferral/reinvestment "
        "relief may still be available, so the connection changes which relief the client gets.",
        "applies": lambda f: f.get("personal", {}).get("venture_capital_investment", 0) > 0,
        "answered": lambda f: _has(f.get("personal", {}), "venture_capital_connection_confirmed"),
        "assumption": "Assumed the investor is not connected with the company, so full EIS/SEIS "
        "income-tax relief was considered.",
    },
    {
        "key": "badr_qualifying_conditions",
        "question": "Does the disposal meet every Business Asset Disposal Relief condition throughout "
        "the two years to disposal — at least 5% of ordinary shares and voting rights, an officer or "
        "employee, and a trading company?",
        "why": "BADR gives the 10% rate only if all conditions are met for the qualifying period; if "
        "any fails, the gain is taxed at the normal CGT rate — a materially different result.",
        "applies": lambda f: f.get("property", {}).get("badr_qualifying_gain", 0) > 0,
        "answered": lambda f: _has(f.get("property", {}), "badr_conditions_confirmed"),
        "assumption": "Assumed all BADR conditions are met (5% shareholding and votes, officer/"
        "employee, trading company, two-year period), so the 10% rate was applied.",
    },
    {
        "key": "termination_penp",
        "question": "Of the termination package, how much is a genuine ex-gratia termination payment, "
        "and how much is post-employment notice pay (PENP) or contractual (e.g. notice, bonus, "
        "restraint of trade, garden leave)?",
        "why": "Only the genuine ex-gratia element gets the £30,000 exemption. PENP and contractual "
        "sums are taxed in full as earnings; if they are wrongly included in the qualifying figure "
        "the tax is understated.",
        "applies": lambda f: f.get("employment", {}).get("termination_payment", 0) > 0,
        "answered": lambda f: _has(f.get("employment", {}), "penp_confirmed"),
        "assumption": "Assumed the whole amount entered is a qualifying ex-gratia termination "
        "payment; any PENP or contractual sums must be taxed in full and excluded from it.",
    },
]


def intake_gaps(facts: dict) -> list[dict]:
    """The unanswered material questions for this client, each with why it
    matters and the assumption the engine is making in its absence."""
    gaps = []
    for check in CHECKS:
        if check["applies"](facts) and not check["answered"](facts):
            gaps.append(
                {
                    "key": check["key"],
                    "question": check["question"],
                    "why": check["why"],
                    "assumption": check["assumption"],
                }
            )
    return gaps
