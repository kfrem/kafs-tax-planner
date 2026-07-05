"""Release impact analysis: which firms' current advice relied on rules a
release just changed (architecture doc §5.5). Pure queries over the
calculator registry's ``consumes`` declarations, the strategy table, and
current advice records — no recomputation, no changes to advice.
"""

from __future__ import annotations

from ruleengine.engine import calculators_consuming
from ruleengine.models import RuleBaseRelease, Strategy, TaxParameter
from ruleengine.taxyear import anchor_date

from .models import AdviceImpactAlert, AdviceRecord


def _strategy_codes_touching(release: RuleBaseRelease) -> set[str]:
    parameter_keys = set(
        TaxParameter.objects.filter(introduced_in_release=release).values_list("key", flat=True)
    )
    calculator_keys = {
        calc for key in parameter_keys for calc in calculators_consuming(key)
    }
    return set(
        Strategy.objects.filter(calculator_key__in=calculator_keys).values_list("code", flat=True)
    )


def _release_covers(release: RuleBaseRelease, tax_year: str) -> bool:
    """Does any parameter row in this release apply to the given tax year?
    Effective dating scopes impact: a 2026/27 rate change does not touch
    2025/26 advice."""
    anchor = anchor_date(tax_year)
    for row in TaxParameter.objects.filter(introduced_in_release=release):
        lower_ok = row.effective_range.lower is None or row.effective_range.lower <= anchor
        upper_ok = row.effective_range.upper is None or anchor < row.effective_range.upper
        if lower_ok and upper_ok:
            return True
    return False


def affected_current_advice(release: RuleBaseRelease) -> list[tuple[AdviceRecord, list[str]]]:
    codes = _strategy_codes_touching(release)
    if not codes:
        return []
    affected = []
    for record in AdviceRecord.objects.filter(superseded_by__isnull=True).select_related("firm", "client"):
        overlap = sorted(
            {r["strategy_code"] for r in record.results} & codes
        )
        if overlap and _release_covers(release, record.tax_year):
            affected.append((record, overlap))
    return affected


def generate_impact_alerts(release: RuleBaseRelease) -> list[AdviceImpactAlert]:
    """Idempotent: an (release, advice record) pair is alerted once."""
    created = []
    for record, overlap in affected_current_advice(release):
        alert, was_created = AdviceImpactAlert.objects.get_or_create(
            release=release,
            advice_record=record,
            defaults={"firm": record.firm, "affected_strategy_codes": overlap},
        )
        if was_created:
            created.append(alert)
    return created
