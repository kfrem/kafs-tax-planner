"""The Advice Generator (architecture doc Section 4): matches client facts
against strategy eligibility, quantifies each applicable strategy through
the calculation engine, attaches citations/timeframe/risk flags, and writes
the immutable AdviceRecord.
"""

from __future__ import annotations

import hashlib
import json

from django.utils import timezone

from ruleengine.engine import CALCULATOR_REGISTRY, parameter_cache, parameter_provenance
from ruleengine.models import RuleBaseRelease, Strategy
from ruleengine.taxyear import anchor_date

from .models import AdviceRecord
from .strategy_adapters import ADAPTERS


class NoReleasedRuleBaseError(Exception):
    pass


def _current_rule_base_release() -> RuleBaseRelease:
    release = (
        RuleBaseRelease.objects.filter(
            status=RuleBaseRelease.Status.RELEASED, effective_date__lte=timezone.now().date()
        )
        .order_by("-effective_date", "-id")
        .first()
    )
    if release is None:
        raise NoReleasedRuleBaseError("No released rule-base version is in force.")
    return release


def _authority_snapshot(strategy: Strategy) -> list[dict]:
    return [
        {
            "citation": a.canonical_citation,
            "type": a.authority_type,
            "uri": a.canonical_uri,
            "status": a.status,
        }
        for a in strategy.authorities.all()
    ]


def generate_advice(client, fact_set, user) -> AdviceRecord:
    tax_year = fact_set.tax_year
    as_of = anchor_date(tax_year)
    release = _current_rule_base_release()

    strategies = Strategy.objects.filter(effective_range__contains=as_of).prefetch_related(
        "authorities"
    )

    results = []
    with parameter_provenance() as parameter_log:
        for strategy in strategies:
            adapter = ADAPTERS.get(strategy.calculator_key)
            if adapter is None or not adapter.is_eligible(fact_set.facts):
                continue

            calculator = CALCULATOR_REGISTRY.get(strategy.calculator_key)
            if calculator is None:
                continue

            calc_facts = adapter.to_facts(fact_set.facts)
            with parameter_cache():
                quantification = calculator(calc_facts, tax_year)

            results.append(
                {
                    "strategy_code": strategy.code,
                    "strategy_name": strategy.name,
                    "tax_domain": strategy.tax_domain,
                    "explanation": strategy.plain_english_explanation,
                    "timeframe": strategy.timeframe,
                    "risk_status": strategy.risk_status,
                    "dotas_notifiable": strategy.dotas_notifiable,
                    "gaar_exposure": strategy.gaar_exposure,
                    "authorities": _authority_snapshot(strategy),
                    "quantification": quantification,
                }
            )

    parameters_used = sorted(parameter_log.values(), key=lambda m: (m["key"], m["tax_year"]))

    facts_json = json.dumps(fact_set.facts, sort_keys=True)
    input_data_hash = hashlib.sha256(facts_json.encode("utf-8")).hexdigest()

    record = AdviceRecord(
        firm=client.firm,
        client=client,
        fact_set=fact_set,
        tax_year=tax_year,
        input_data_hash=input_data_hash,
        input_data_snapshot=fact_set.facts,
        rule_base_release=release,
        results=results,
        parameters_used=parameters_used,
        generated_by=user,
    )
    record.save()
    return record
