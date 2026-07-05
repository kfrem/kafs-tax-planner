"""The independent expert panel: four reviewer personas that examine a
generated advice record BEFORE the human professional sees it, exactly as
a supporting team would — then the professional approves, rejects, or
redirects on their evidence.

Design constraints (architecture doc Section 8): each persona is a
DETERMINISTIC rule set codifying what that professional checks. No LLM,
no non-reproducible judgement: a panel review of the same advice record
under the same rule base always produces the same findings, so the review
itself is audit evidence. An optional LLM narrative layer per persona is
a Phase 2+ addition under the Section 8 guardrails; it must only ever
*explain* these findings, never add or remove them.

Severities:
  blocker   — must be resolved before approval (or overridden with a
              written note, which the decision workflow enforces)
  caution   — the professional must actively consider this
  info      — context the professional should see
"""

from __future__ import annotations

from authority.models import Authority
from ruleengine.engine import CALCULATOR_REGISTRY, parameter_cache

from .strategy_adapters import ADAPTERS

LOWER_EARNINGS_LIMIT = 6500  # 2025/26, £125/week: NI qualifying-year floor


def _finding(persona, code, severity, message, strategy=None):
    return {
        "persona": persona,
        "code": code,
        "severity": severity,
        "message": message,
        "strategy": strategy,
    }


def _mix(record):
    for r in record.results:
        if r["strategy_code"] == "salary-dividend-mix":
            return r["quantification"]
    return None


def _quant(record, code):
    for r in record.results:
        if r["strategy_code"] == code:
            return r["quantification"]
    return None


class TaxAccountantReviewer:
    """Checks the numbers the way a reviewing accountant would: can I
    reproduce them, do they internally balance, and where is relief
    being wasted?"""

    persona = "tax_accountant"

    def review(self, record):
        findings = []

        # A1 — independent recomputation: re-run every strategy from the
        # immutable input snapshot against the CURRENT released rule base.
        # Any difference means the rules have moved since generation (or an
        # engine change altered behaviour): the advice must be regenerated,
        # not approved.
        drifted = []
        for r in record.results:
            strategy_code = r["strategy_code"]
            calculator_key = self._calculator_key_for(record, strategy_code)
            adapter = ADAPTERS.get(calculator_key)
            calculator = CALCULATOR_REGISTRY.get(calculator_key)
            if adapter is None or calculator is None:
                drifted.append(strategy_code)
                continue
            with parameter_cache():
                fresh = calculator(adapter.to_facts(record.input_data_snapshot), record.tax_year)
            if fresh != r["quantification"]:
                drifted.append(strategy_code)
        if drifted:
            findings.append(_finding(
                self.persona, "A1_NOT_REPRODUCIBLE", "blocker",
                "Independent recomputation from the stored input snapshot no longer "
                f"matches the advice for: {', '.join(drifted)}. The rule base or engine "
                "has changed since generation — regenerate before approving.",
            ))
        else:
            findings.append(_finding(
                self.persona, "A1_RECOMPUTED_OK", "info",
                "All strategy figures independently recomputed from the stored input "
                "snapshot under the current released rule base: identical to the penny.",
            ))

        # A2 — extraction arithmetic must balance on every comparison row.
        mix = _mix(record)
        if mix:
            for row in mix["comparisons"]:
                expected = round(
                    row["salary"] + row["dividends_available"]
                    - row["employee_nic"] - row["personal_tax_on_extraction"], 2,
                )
                if abs(expected - row["net_to_individual"]) > 0.02:
                    findings.append(_finding(
                        self.persona, "A2_IDENTITY_BROKEN", "blocker",
                        f"Salary option {row['salary']:,}: net figure does not equal "
                        "salary + dividends − NIC − tax. Engine defect; do not approve.",
                        "salary-dividend-mix",
                    ))

        # A3/A4 — wasted relief and allowance charges.
        pension = _quant(record, "pension-annual-allowance-carry-forward")
        if pension:
            unrelieved = pension["personal_route"]["unrelieved_amount"]
            if unrelieved > 0:
                findings.append(_finding(
                    self.persona, "A3_UNRELIEVED_CONTRIBUTION", "caution",
                    f"£{unrelieved:,.0f} of the desired personal contribution exceeds relevant "
                    "UK earnings and attracts no relief. Discuss the employer route or a "
                    "reduced contribution before the client commits funds.",
                    "pension-annual-allowance-carry-forward",
                ))
            charge_basis = pension["amount_subject_to_annual_allowance_charge"]
            if charge_basis > 0:
                findings.append(_finding(
                    self.persona, "A4_AA_CHARGE_EXPOSURE", "caution",
                    f"£{charge_basis:,.0f} of the desired contribution exceeds the available "
                    "annual allowance (including carry-forward) and would trigger an annual "
                    "allowance charge at the client's marginal rate.",
                    "pension-annual-allowance-carry-forward",
                ))

        # A5 — provenance must exist (audit integrity).
        if not record.parameters_used:
            findings.append(_finding(
                self.persona, "A5_NO_PROVENANCE", "blocker",
                "This advice record has no rule provenance (generated before provenance "
                "capture). Regenerate so the defence file is complete.",
            ))

        return findings

    @staticmethod
    def _calculator_key_for(record, strategy_code):
        from ruleengine.models import Strategy

        strategy = Strategy.objects.filter(code=strategy_code).first()
        return strategy.calculator_key if strategy else None


class TaxLawyerReviewer:
    """Checks the legal footing: is every position cited, is every cited
    authority still good law, and are disclosure duties met?"""

    persona = "tax_lawyer"

    def review(self, record):
        findings = []

        cited = set()
        for r in record.results:
            if not r["authorities"]:
                findings.append(_finding(
                    self.persona, "L1_NO_CITATION", "blocker",
                    f"'{r['strategy_name']}' carries no legal authority. An uncited "
                    "position must not reach a client.",
                    r["strategy_code"],
                ))
            for a in r["authorities"]:
                cited.add(a["citation"])

        # L2 — live status of every cited authority, checked against the
        # registry NOW (a case may have been overruled since generation).
        for authority in Authority.objects.filter(canonical_citation__in=cited):
            if authority.status == Authority.Status.OVERRULED:
                findings.append(_finding(
                    self.persona, "L2_AUTHORITY_OVERRULED", "blocker",
                    f"{authority.canonical_citation} has been marked OVERRULED in the "
                    "authority registry. Every strategy relying on it needs editorial "
                    "review before any advice citing it is approved.",
                ))
            elif authority.status not in (Authority.Status.IN_FORCE,):
                findings.append(_finding(
                    self.persona, "L2_AUTHORITY_STATUS", "caution",
                    f"{authority.canonical_citation} is marked '{authority.status}'. "
                    "Verify the current text/holding against the primary source before "
                    "relying on it.",
                ))

        # L3/L4 — disclosure duties on flagged strategies.
        for r in record.results:
            if r["risk_status"] != "settled":
                findings.append(_finding(
                    self.persona, "L3_RISK_DISCLOSURE", "caution",
                    f"'{r['strategy_name']}' is {r['risk_status'].upper()}. PCRT requires "
                    "the client to understand the risk before acting; record that "
                    "conversation.",
                    r["strategy_code"],
                ))
            if r.get("dotas_notifiable") or r.get("gaar_exposure"):
                findings.append(_finding(
                    self.persona, "L4_DOTAS_GAAR", "caution",
                    f"'{r['strategy_name']}' carries DOTAS/GAAR flags — confirm disclosure "
                    "position and document the advice boundary.",
                    r["strategy_code"],
                ))

        # L5 — settlements legislation on spousal dividend structures.
        spouse_income = record.input_data_snapshot.get("personal", {}).get("spouse_income", 0)
        if _mix(record) and spouse_income:
            findings.append(_finding(
                self.persona, "L5_SETTLEMENTS", "info",
                "Married owner-manager with dividend extraction: if shares are (to be) "
                "held by the spouse, they must be full ordinary shares — Jones v Garnett "
                "[2007] UKHL 35 protects outright gifts of ordinary shares, not "
                "income-only rights.",
                "salary-dividend-mix",
            ))

        # L6/L7 — IHT formalities.
        if _quant(record, "iht-spousal-transfer-and-nil-rate-bands"):
            findings.append(_finding(
                self.persona, "L6_TNRB_CLAIM", "info",
                "Transferred nil-rate bands are claimed by the survivor's personal "
                "representatives within two years of the second death (IHTA 1984 s.8B). "
                "Check the wills actually implement the mirror structure assumed.",
                "iht-spousal-transfer-and-nil-rate-bands",
            ))
        if _quant(record, "iht-lifetime-gifting-pets"):
            findings.append(_finding(
                self.persona, "L7_GWR", "caution",
                "The planned gift must be outright with no retained benefit, or the "
                "gift-with-reservation rules (FA 1986 s.102) put it straight back in the "
                "estate. Document the gift and the donor's continued means.",
                "iht-lifetime-gifting-pets",
            ))

        return findings


class HMRCConsultantReviewer:
    """Reads the advice the way an inspector would: what gets scrutinised,
    what must be filed, what paperwork must exist."""

    persona = "hmrc_consultant"

    def review(self, record):
        findings = []

        mix = _mix(record)
        if mix and mix.get("recommended"):
            salary = mix["recommended"]["salary"]
            if 0 <= salary < LOWER_EARNINGS_LIMIT:
                findings.append(_finding(
                    self.persona, "H1_BELOW_LEL", "caution",
                    f"Recommended salary £{salary:,} is below the Lower Earnings Limit "
                    f"(£{LOWER_EARNINGS_LIMIT:,}): no qualifying year for State Pension. "
                    "Confirm the client's NI record can afford the gap or step up to the LEL.",
                    "salary-dividend-mix",
                ))
            findings.append(_finding(
                self.persona, "H7_DIVIDEND_PAPERWORK", "info",
                "Dividends need board minutes, vouchers, and distributable reserves "
                "(CA 2006 Part 23) — HMRC recharacterises undocumented drawings in "
                "enquiry. Confirm the company's paperwork discipline.",
                "salary-dividend-mix",
            ))

        incorporation = _quant(record, "incorporation-vs-sole-trade")
        if incorporation:
            findings.append(_finding(
                self.persona, "H3_COMMERCIAL_PURPOSE", "caution",
                "Any incorporation/disincorporation decision should have documented "
                "commercial reasoning beyond the tax comparison — HMRC scrutinises "
                "tax-only incorporations.",
                "incorporation-vs-sole-trade",
            ))

        pension = _quant(record, "pension-annual-allowance-carry-forward")
        if pension:
            if pension["amount_subject_to_annual_allowance_charge"] > 0:
                findings.append(_finding(
                    self.persona, "H5_AA_REPORTING", "caution",
                    "An annual allowance charge must be self-assessed; consider whether "
                    "Scheme Pays is available and ensure the charge is returned.",
                    "pension-annual-allowance-carry-forward",
                ))
            employer = pension.get("employer_route")
            company = record.input_data_snapshot.get("company", {})
            profit = company.get("profit_before_remuneration", 0)
            if employer and profit and employer["contribution"] > 0.5 * profit:
                findings.append(_finding(
                    self.persona, "H4_WHOLLY_EXCLUSIVELY", "caution",
                    "Employer contribution exceeds half of profit: be ready to evidence "
                    "the whole remuneration package as wholly and exclusively for the "
                    "trade (CTA 2009 s.54).",
                    "pension-annual-allowance-carry-forward",
                ))

        estate = record.input_data_snapshot.get("estate", {}) or {}
        combined = estate.get("combined_estate_second_death", 0)
        if combined and abs(combined - 2000000) <= 300000:
            findings.append(_finding(
                self.persona, "H6_TAPER_CLIFF", "info",
                "The estate sits near the £2m RNRB taper threshold: valuations will be "
                "scrutinised. Commission robust professional valuations before relying "
                "on taper-sensitive planning.",
            ))

        return findings


class BusinessExpertReviewer:
    """Asks whether the tax-optimal answer is commercially sensible for
    this client's cash flow, liquidity, and life plans."""

    persona = "business_expert"

    def review(self, record):
        findings = []
        facts = record.input_data_snapshot

        mix = _mix(record)
        if mix and mix.get("recommended"):
            rec = mix["recommended"]
            profit = mix["profit_before_remuneration"]
            gross_extraction = rec["salary"] + rec["dividends_available"]
            if profit and gross_extraction > 0.85 * profit:
                findings.append(_finding(
                    self.persona, "B1_WORKING_CAPITAL", "caution",
                    f"The optimal extraction takes £{gross_extraction:,.0f} of "
                    f"£{profit:,.0f} profit out of the company. Confirm working-capital "
                    "and investment needs before extracting at this level.",
                    "salary-dividend-mix",
                ))
            # B4 — price the NI qualifying year so the trade-off is explicit.
            if rec["salary"] < LOWER_EARNINGS_LIMIT:
                at_or_above = [c for c in mix["comparisons"] if c["salary"] >= LOWER_EARNINGS_LIMIT]
                if at_or_above:
                    best_above = max(at_or_above, key=lambda c: c["net_to_individual"])
                    cost = round(rec["net_to_individual"] - best_above["net_to_individual"], 2)
                    findings.append(_finding(
                        self.persona, "B4_NI_YEAR_PRICE", "info",
                        f"Securing this year's State Pension qualifying year (salary "
                        f"£{best_above['salary']:,}) costs £{cost:,.2f} against the "
                        "tax-optimal mix — usually cheap insurance; put the choice to "
                        "the client explicitly.",
                        "salary-dividend-mix",
                    ))

        pension = _quant(record, "pension-annual-allowance-carry-forward")
        if pension and pension["desired_contribution"] > 0:
            findings.append(_finding(
                self.persona, "B2_LIQUIDITY_LOCKUP", "info",
                f"£{pension['desired_contribution']:,.0f} into pension is locked until "
                "normal minimum pension age (57 from April 2028). Confirm accessible "
                "reserves cover foreseeable needs first.",
                "pension-annual-allowance-carry-forward",
            ))

        gifting = _quant(record, "iht-lifetime-gifting-pets")
        estate = facts.get("estate", {}) or {}
        basis = estate.get("combined_estate_second_death") or max(
            0, estate.get("gross_value", 0) - estate.get("liabilities", 0)
        )
        if gifting and basis:
            gift = gifting["planned_gift"]
            if gift > 0.10 * basis:
                findings.append(_finding(
                    self.persona, "B3_GIFT_AFFORDABILITY", "caution",
                    f"The planned gift is {gift / basis:.0%} of the estate. Stress-test "
                    "the donor's own longevity, care-cost, and income needs before "
                    "giving capital away irrevocably.",
                    "iht-lifetime-gifting-pets",
                ))

        return findings


REVIEWERS = [
    TaxAccountantReviewer(),
    TaxLawyerReviewer(),
    HMRCConsultantReviewer(),
    BusinessExpertReviewer(),
]

_SEVERITY_TO_VERDICT = {"blocker": "blocked", "caution": "attention"}


def deploy_panel(record, user):
    """Run all four reviewers against an advice record and store the
    review. Returns the saved PanelReview."""
    from .models import PanelReview

    findings = []
    verdicts = {}
    for reviewer in REVIEWERS:
        persona_findings = reviewer.review(record)
        findings.extend(persona_findings)
        severities = {f["severity"] for f in persona_findings}
        if "blocker" in severities:
            verdicts[reviewer.persona] = "blocked"
        elif "caution" in severities:
            verdicts[reviewer.persona] = "attention"
        else:
            verdicts[reviewer.persona] = "clear"

    if "blocked" in verdicts.values():
        verdicts["overall"] = "blocked"
    elif "attention" in verdicts.values():
        verdicts["overall"] = "attention"
    else:
        verdicts["overall"] = "clear"

    review = PanelReview(
        firm=record.firm,
        advice_record=record,
        findings=findings,
        verdicts=verdicts,
        requested_by=user,
    )
    review.save()
    return review


class DecisionError(Exception):
    pass


def record_decision(record, user, decision, notes=""):
    """The professional's decision — only possible on the evidence of a
    panel review of this exact record, and blockers can only be approved
    over with a written override note."""
    from .models import ProfessionalDecision

    review = record.latest_panel_review
    if review is None:
        raise DecisionError(
            "The expert panel has not reviewed this advice yet. Deploy the panel first."
        )
    if decision == ProfessionalDecision.Decision.APPROVED and review.blockers and not notes.strip():
        raise DecisionError(
            "The panel raised blockers. Approving over a blocker requires a written "
            "override note explaining the professional judgement."
        )
    if decision in (
        ProfessionalDecision.Decision.REJECTED,
        ProfessionalDecision.Decision.NEEDS_REVISION,
    ) and not notes.strip():
        raise DecisionError("Rejecting or requesting revision requires a note for the file.")

    professional_decision = ProfessionalDecision(
        firm=record.firm,
        advice_record=record,
        panel_review=review,
        decision=decision,
        notes=notes,
        decided_by=user,
    )
    professional_decision.save()
    return professional_decision


# --- Persona voices (explain-only, architecture doc §8) -----------------------

PERSONA_TITLES = {
    "tax_accountant": "Tax accountant",
    "tax_lawyer": "Tax lawyer",
    "hmrc_consultant": "HMRC consultant",
    "business_expert": "Business expert",
}

_VERDICT_PHRASES = {
    "clear": "raises no concerns",
    "attention": "asks the professional to consider the following before approving",
    "blocked": "BLOCKS approval until the following are resolved",
}


def persona_summaries(review) -> list[dict]:
    """Deterministic prose per reviewer persona, composed ONLY from that
    persona's stored findings. This is the explain-only boundary an LLM
    voice would also live behind: a voice may re-express findings, never
    add, remove, or renumber them."""
    summaries = []
    for persona, title in PERSONA_TITLES.items():
        persona_findings = [f for f in review.findings if f["persona"] == persona]
        verdict = review.verdicts.get(persona, "clear")
        lead = f"The {title.lower()} {_VERDICT_PHRASES[verdict]}."
        ordered = sorted(
            persona_findings,
            key=lambda f: {"blocker": 0, "caution": 1, "info": 2}[f["severity"]],
        )
        summaries.append(
            {
                "persona": persona,
                "title": title,
                "verdict": verdict,
                "lead": lead,
                "points": [
                    {"severity": f["severity"], "message": f["message"]} for f in ordered
                ],
            }
        )
    return summaries
