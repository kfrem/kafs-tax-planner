"""Plain-English glossary. Every term an accountant (or their client) might not
instantly grasp gets three layers: a one-line meaning, a fuller explanation, and
a "how to put it to the client" line. Surfaced as click-to-drill-down popovers
via the ``{% explain %}`` template tag and listed in full on the Glossary page.

Keep the language plain — this is the layer that lets a practitioner turn a
technical screen into advice a client understands.
"""

from __future__ import annotations

# key -> (term, plain one-liner, fuller detail, how to say it to a client)
GLOSSARY = {
    # --- The software's own machinery ---
    "expert_panel": (
        "Expert panel",
        "Four automated reviewers that check the advice before you sign it off.",
        "Before any advice reaches you for approval, four independent reviewer 'lenses' "
        "examine it: a tax accountant (re-checks every figure), a tax lawyer (checks the "
        "law and citations), an HMRC consultant (what an inspector would query), and a "
        "business expert (is it commercially sensible). Each flags what it finds; you make "
        "the final call.",
        "\"Every calculation is independently double-checked from four angles before I rely on it.\"",
    ),
    "blocker": (
        "Blocker",
        "A serious issue that stops approval until you resolve it or override it in writing.",
        "The panel raises a blocker when something must not reach a client unresolved — for "
        "example, a figure that can no longer be reproduced, or a strategy with no legal "
        "citation. You cannot approve over a blocker without recording a written reason.",
        "\"The system refused to let me pass this until I'd dealt with a specific problem.\"",
    ),
    "caution": (
        "Caution",
        "A point you must actively consider before approving — not a stopper.",
        "A caution flags a matter of judgement: a disclosure duty, a commercial risk, a "
        "paperwork requirement. The advice can still be approved, but you should have "
        "considered and, where needed, documented it.",
        "\"There's a judgement call here I've weighed up on your behalf.\"",
    ),
    "recomputation": (
        "Independent recomputation",
        "The engine re-does every calculation from scratch to confirm it still matches.",
        "The accountant reviewer re-runs every figure from the stored client facts against "
        "the current rulebook. If anything differs — even by a penny — it blocks approval, "
        "because it means the rules have changed since the advice was produced. This is what "
        "makes the numbers reproducible and defensible.",
        "\"The figures aren't a one-off — they can be reproduced exactly, any time.\"",
    ),
    "provenance": (
        "Provenance",
        "The record of exactly which rules, rates and law produced each number.",
        "For every figure, the software stores which tax parameters and legal authorities "
        "were used and which rulebook version was in force. That's your defence file if HMRC "
        "ever asks how a number was arrived at.",
        "\"I can show precisely which rules and law each figure is based on.\"",
    ),
    "rule_base": (
        "Rule base",
        "The dated set of tax rates, thresholds and rules the engine calculates from.",
        "Rather than hard-coding tax rates, the software holds them as dated data with "
        "effective dates, so it always applies the right figures for the right tax year and "
        "keeps the history. A version is only used once two people have signed it off.",
        "\"The tax rates it uses are version-controlled and signed off — not guesswork.\"",
    ),
    "risk_status": (
        "Risk status",
        "Whether a strategy is settled law or a matter of judgement.",
        "'Settled' means the position is well-established and low-risk. 'Borderline' means it "
        "depends on facts or professional judgement and carries a caveat — the client must "
        "understand the risk before acting.",
        "\"This one is standard practice / this one needs a judgement call we should discuss.\"",
    ),
    "impact_alert": (
        "Impact alert",
        "A flag that a rule change affects advice you already gave.",
        "When a tax rate or rule changes, the software identifies which previously issued "
        "advice is affected, so you can proactively revisit it rather than find out later.",
        "\"If the rules change, I'll know which of your plans need a second look.\"",
    ),

    # --- Tax concepts on the advice screens ---
    "marginal_rate": (
        "Marginal rate",
        "The rate of tax on the next pound of income.",
        "Because UK tax is banded, an extra pound of income may be taxed at 20%, 40%, 45% (or "
        "more where allowances taper). The marginal rate is what matters when deciding whether "
        "to take more income, contribute to a pension, or defer.",
        "\"The tax on your next slice of income is X% — that's what drives these decisions.\"",
    ),
    "personal_allowance_taper": (
        "Personal-allowance taper",
        "The tax-free personal allowance is withdrawn between £100,000 and £125,140 of income.",
        "For every £2 of income over £100,000 you lose £1 of personal allowance, fully gone by "
        "£125,140. This creates an effective 60% band, which is why pension contributions or "
        "Gift Aid in that range can be so valuable.",
        "\"In this income band you effectively lose 60p in the pound — but we can claw some back.\"",
    ),
    "annual_allowance": (
        "Pension annual allowance",
        "The most you can put into pensions each year with tax relief (£60,000 for 2025/26).",
        "Contributions above the annual allowance trigger a tax charge. High earners have it "
        "'tapered' down. Unused allowance from the previous three years can be 'carried "
        "forward'.",
        "\"There's a yearly cap on tax-relieved pension saving — but unused room can be brought forward.\"",
    ),
    "carry_forward": (
        "Carry-forward",
        "Using unused pension allowance from the last three years.",
        "If you didn't use your full annual allowance in the previous three years, you can add "
        "that unused amount to this year's, allowing a larger tax-relieved contribution.",
        "\"You can top up using unused pension room from earlier years.\"",
    ),
    "lower_earnings_limit": (
        "Lower Earnings Limit (LEL)",
        "The salary level that secures a qualifying year for the State Pension.",
        "A salary at or above the LEL (about £6,500 a year) counts as a qualifying year toward "
        "the State Pension without actually paying NIC. A very low director's salary can "
        "accidentally miss it.",
        "\"Keeping your salary at this level protects your State Pension for the year — cheaply.\"",
    ),
    "settlements": (
        "Settlements legislation",
        "Anti-avoidance rules on shifting income to a spouse or family member.",
        "If income is diverted to a lower-taxed family member without a genuine outright gift of "
        "real ownership, HMRC can tax it back on the original person. Jones v Garnett confirmed "
        "gifts of full ordinary shares between spouses are protected.",
        "\"Splitting income with your spouse works — but only with a genuine gift of real shares.\"",
    ),
    "gift_with_reservation": (
        "Gift with reservation (GWR)",
        "Giving something away but still benefiting from it — so it stays in your estate for IHT.",
        "If you give an asset away but keep using or benefiting from it (e.g. give the house but "
        "keep living in it rent-free), inheritance tax treats it as if you never gave it away.",
        "\"To save inheritance tax the gift must be genuine — you can't keep the benefit of it.\"",
    ),
    "nil_rate_band": (
        "Nil-rate band (NRB)",
        "The slice of an estate that's free of inheritance tax (£325,000).",
        "The first £325,000 of an estate is taxed at 0%. There's an additional 'residence' "
        "nil-rate band for a home passing to direct descendants, and unused bands transfer to a "
        "surviving spouse.",
        "\"The first £325,000 (more with a home to children) passes tax-free.\"",
    ),
    "rnrb_taper": (
        "RNRB taper",
        "The extra home allowance is withdrawn on estates over £2m.",
        "The residence nil-rate band (extra IHT-free allowance for a home left to descendants) is "
        "reduced by £1 for every £2 the estate exceeds £2m. Valuations near this cliff get "
        "scrutinised.",
        "\"Large estates lose the extra home allowance — worth planning around the £2m line.\"",
    ),
    "dotas": (
        "DOTAS",
        "Disclosure of Tax Avoidance Schemes — rules requiring certain schemes to be reported to HMRC.",
        "If a strategy has hallmarks of a disclosable avoidance scheme, it must be notified to "
        "HMRC. The planner flags where this needs checking so the disclosure position is clear.",
        "\"Some aggressive schemes must be reported to HMRC — none of this is that, but we check.\"",
    ),
    "gaar": (
        "GAAR",
        "General Anti-Abuse Rule — HMRC's power to counteract abusive tax arrangements.",
        "The GAAR lets HMRC undo arrangements that are 'abusive' — not just any tax saving, but "
        "contrived steps with no real commercial purpose. The planner flags where a position "
        "should be checked against it.",
        "\"Sensible planning is fine; contrived schemes can be undone — we stay the right side of that line.\"",
    ),
    "pcrt": (
        "PCRT",
        "Professional Conduct in Relation to Taxation — the ethical standard for tax advisers.",
        "The PCRT is the standards framework your professional body holds you to. It requires, "
        "for example, that clients understand the risks of a position before acting on it.",
        "(An internal professional-standards reference — it governs how advice must be given.)",
    ),
    "wholly_exclusively": (
        "Wholly and exclusively",
        "The test for whether a business cost is tax-deductible.",
        "A cost is only deductible against business profits if incurred wholly and exclusively "
        "for the trade. Large owner-related payments (e.g. big pension contributions) may need "
        "evidence they meet this test.",
        "\"For a cost to be deductible it has to be genuinely for the business.\"",
    ),
    "badr": (
        "Business Asset Disposal Relief (BADR)",
        "A reduced capital-gains-tax rate when you sell a qualifying business.",
        "BADR taxes qualifying business sale gains at 10% (rising to 18% from April 2026) instead "
        "of the normal rate, up to a £1m lifetime limit — but only if you meet all the conditions "
        "(shareholding, officer/employee, trading, 2-year period).",
        "\"Selling your business can qualify for a lower CGT rate — if the conditions are met.\"",
    ),
    "s24": (
        "Section 24 (landlord finance-cost restriction)",
        "Residential landlords only get 20% tax relief on mortgage interest.",
        "Since 2020, individual residential landlords can't deduct mortgage interest as an "
        "expense; instead they get a 20% tax reducer. Higher-rate landlords therefore pay more "
        "than they might expect — a key driver of the 'incorporate?' question.",
        "\"Your mortgage interest only gets 20% relief now — which changes the sums on your lets.\"",
    ),
    "eis_seis_vct": (
        "EIS / SEIS / VCT",
        "Government-backed schemes giving income-tax relief for investing in young companies.",
        "These give income-tax relief (30%/50%/30%) for investing in qualifying smaller or "
        "start-up companies, with capital-gains advantages too. Higher risk, so suitability "
        "matters.",
        "\"Investing in qualifying young companies can cut your income tax — but it's higher risk.\"",
    ),
    "termination_payment": (
        "Termination payment (£30,000 exemption)",
        "The first £30,000 of a genuine ex-gratia leaving payment is tax-free.",
        "When employment ends, a genuine (non-contractual) termination payment is exempt up to "
        "£30,000; the excess is taxed as the top slice of income. Contractual pay and "
        "post-employment notice pay (PENP) are taxed in full.",
        "\"The first £30,000 of a genuine pay-off is tax-free — but only the genuine part.\"",
    ),
}


def get(key):
    return GLOSSARY.get(key)


def all_terms():
    """Alphabetical list of (key, term, plain, detail, client) for the glossary page."""
    return sorted(
        ({"key": k, "term": v[0], "plain": v[1], "detail": v[2], "client": v[3]}
         for k, v in GLOSSARY.items()),
        key=lambda e: e["term"].lower(),
    )
