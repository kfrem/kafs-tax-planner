"""Editorial pre-check: the machine's review of the rule base BEFORE the
human tax editor's sign-off (architecture doc §5.6).

What the machine can honestly verify:
  - internal consistency: every parameter is consumed by a registered
    calculator, every strategy is fully wired (calculator, adapter,
    authorities, explanation, risk, timeframe) and evidenced by golden
    or persona tests;
  - the authority registry: every authority has a live, fetchable
    primary-source URI (via the watchers' snapshots) and an in-force
    status;
  - source cross-references: each parameter's figures searched for in
    the fetched text of the watched primary sources, so the reviewer
    sees WHERE a number is corroborated.

What the machine cannot do: exercise professional judgement that the
right sections were chosen and the explanations are sound. That is the
human editor's YES.
"""

from __future__ import annotations

import datetime

from django.db.models import Q

from authority.models import Authority
from monitoring.models import WatchedSource

from .engine import CALCULATOR_REGISTRY, calculators_consuming
from .models import GoldenTestCase, Strategy, TaxParameter

CURRENT_ANCHOR = datetime.date(2025, 4, 6)
# The review also covers scheduled future-tax-year rows (e.g. the BADR rate
# rise on 6 April 2026), so a row that is staged but not yet in force is
# still machine-reviewed and appears in the sign-off pack before its release
# is approved. A parameter whose open effective range spans both anchors is
# returned once; a rate that changes across the boundary shows as two rows.
REVIEW_ANCHORS = (CURRENT_ANCHOR, datetime.date(2026, 4, 6))


def _current_parameters():
    anchors = Q()
    for anchor in REVIEW_ANCHORS:
        anchors |= Q(effective_range__contains=anchor)
    return (
        TaxParameter.objects.filter(anchors)
        .select_related("introduced_in_release")
        .order_by("tax_domain", "key", "id")
    )


def _numbers_in(payload, out=None):
    out = out if out is not None else set()
    if isinstance(payload, bool):
        return out
    if isinstance(payload, (int, float)):
        if abs(payload) >= 100:  # thresholds/amounts, not rates
            out.add(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            _numbers_in(value, out)
    elif isinstance(payload, list):
        for value in payload:
            _numbers_in(value, out)
    return out


def _source_evidence(parameter) -> list[str]:
    """Which watched primary-source texts mention this parameter's figures."""
    evidence = []
    numbers = _numbers_in(parameter.payload)
    if not numbers:
        return evidence
    snapshots = list(
        WatchedSource.objects.exclude(last_content_snapshot="").values_list(
            "label", "last_content_snapshot"
        )
    )
    for number in sorted(numbers):
        formatted = {f"{number:,.0f}", f"{number:.0f}"}
        hits = [
            label
            for label, snapshot in snapshots
            if any(f in snapshot for f in formatted)
        ]
        if hits:
            evidence.append(f"{number:,.0f} appears in: {'; '.join(sorted(set(hits))[:3])}")
    return evidence


def precheck() -> dict:
    """Runs every machine check; returns a structured report. No writes."""
    report = {"parameters": [], "strategies": [], "authorities": [], "failures": 0}

    golden_keys = set(GoldenTestCase.objects.values_list("calculator_key", flat=True))

    for parameter in _current_parameters():
        checks = []
        consumers = calculators_consuming(parameter.key)
        checks.append(("consumed by a registered calculator", bool(consumers),
                       ", ".join(consumers) or "NONE"))
        golden = [c for c in consumers if c in golden_keys]
        checks.append(("figure exercised by golden test cases", bool(golden),
                       ", ".join(golden) or "no direct golden case"))
        released = parameter.introduced_in_release.status == "released"
        checks.append(("belongs to a released rule-base version", released,
                       parameter.introduced_in_release.version))
        report["parameters"].append({
            "key": parameter.key,
            "label": parameter.label,
            "domain": parameter.tax_domain,
            "payload": parameter.payload,
            "release": parameter.introduced_in_release.version,
            "checks": checks,
            "source_evidence": _source_evidence(parameter),
        })
        report["failures"] += sum(1 for _, ok, _ in checks if not ok)

    from advice.strategy_adapters import ADAPTERS

    for strategy in Strategy.objects.prefetch_related("authorities").order_by("tax_domain", "code"):
        authorities = list(strategy.authorities.all())
        checks = [
            ("calculator registered", strategy.calculator_key in CALCULATOR_REGISTRY, strategy.calculator_key),
            ("adapter registered", strategy.calculator_key in ADAPTERS, ""),
            ("has legal authorities", bool(authorities), f"{len(authorities)} cited"),
            ("plain-English explanation present", len(strategy.plain_english_explanation) >= 150,
             f"{len(strategy.plain_english_explanation)} chars"),
            ("risk status set", bool(strategy.risk_status), strategy.risk_status),
            ("timeframe set", bool(strategy.timeframe), strategy.timeframe),
        ]
        report["strategies"].append({
            "code": strategy.code,
            "name": strategy.name,
            "domain": strategy.tax_domain,
            "risk": strategy.risk_status,
            "timeframe": strategy.timeframe,
            "explanation": strategy.plain_english_explanation,
            "authorities": [(a.canonical_citation, a.canonical_uri, a.status) for a in authorities],
            "checks": checks,
        })
        report["failures"] += sum(1 for _, ok, _ in checks if not ok)

    for authority in Authority.objects.order_by("canonical_citation"):
        watched = authority.watched_sources.first()
        snapshot_length = len(watched.last_content_snapshot) if watched else 0
        checks = [
            ("canonical URI recorded", bool(authority.canonical_uri), authority.canonical_uri),
            ("primary source fetched by watcher", snapshot_length > 200,
             f"{snapshot_length:,} chars of source text on file"),
            ("status is in force", authority.status == Authority.Status.IN_FORCE, authority.status),
            ("verbatim extract on file", len(authority.verbatim_extract) >= 50, ""),
        ]
        report["authorities"].append({
            "citation": authority.canonical_citation,
            "type": authority.get_authority_type_display(),
            "uri": authority.canonical_uri,
            "extract": authority.verbatim_extract,
            "checks": checks,
        })
        report["failures"] += sum(1 for _, ok, _ in checks if not ok)

    return report
