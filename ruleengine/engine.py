"""The deterministic calculation engine (architecture doc Section 5.3).

Calculators are pure Python functions: given a client fact set and a tax
year, they return the same answer every time, reading parameters only
through ``get_parameter`` so every calculator is registered against the
rule identifiers it consumes. This is what makes "which advice is affected
if this rule changes?" a query, not a memory exercise.
"""

from __future__ import annotations

import contextlib
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable

from .models import TaxParameter
from .taxyear import anchor_date, tax_year_bounds


class RuleNotFoundError(Exception):
    """Raised when no TaxParameter row covers the requested key/tax year."""


# Scoped cache for parameter lookups. Deliberately NOT a module-level
# lru_cache: the rule base is editable at runtime via Django Admin, so a
# process-lifetime cache could serve stale rules after a release. The cache
# lives only inside an explicit `with parameter_cache():` block — one advice
# generation or one optimiser scan — within which the rule base is
# necessarily constant.
_parameter_cache: ContextVar[dict | None] = ContextVar("parameter_cache", default=None)

# Provenance log: while active, every parameter row resolved is recorded so
# the advice record can store exactly which rows (and hence which rule-base
# releases) produced its numbers (architecture doc Section 6.2).
_parameter_log: ContextVar[dict | None] = ContextVar("parameter_log", default=None)


@contextlib.contextmanager
def parameter_cache():
    token = _parameter_cache.set({})
    try:
        yield
    finally:
        _parameter_cache.reset(token)


@contextlib.contextmanager
def parameter_provenance():
    """Yields a dict that fills with {(key, tax_year): row metadata} for
    every parameter resolved while the context is active."""
    token = _parameter_log.set({})
    try:
        yield _parameter_log.get()
    finally:
        _parameter_log.reset(token)


def get_parameter(key: str, tax_year: str) -> dict:
    """Look up the payload of the TaxParameter effective during ``tax_year``.

    Only rows introduced by a RELEASED rule-base release are visible: a
    parameter staged under a draft release must never influence advice
    (Section 5.6 four-eyes governance). Uses the PostgreSQL date-range
    containment operator via Django's ``__contains`` lookup.
    """
    cache = _parameter_cache.get()
    log = _parameter_log.get()
    cache_key = (key, tax_year)

    if cache is not None and cache_key in cache:
        entry = cache[cache_key]
        if log is not None:
            log[cache_key] = entry["meta"]
        return entry["payload"]

    as_of = anchor_date(tax_year)
    param = (
        TaxParameter.objects.filter(
            key=key,
            effective_range__contains=as_of,
            introduced_in_release__status="released",
        )
        .select_related("introduced_in_release")
        .order_by("-id")
        .first()
    )
    if param is None:
        raise RuleNotFoundError(f"No released TaxParameter for key={key!r} effective in {tax_year}")

    meta = {
        "key": key,
        "tax_year": tax_year,
        "parameter_id": param.pk,
        "effective_from": param.effective_range.lower.isoformat(),
        "release": param.introduced_in_release.version,
    }
    if cache is not None:
        cache[cache_key] = {"payload": param.payload, "meta": meta}
    if log is not None:
        log[cache_key] = meta
    return param.payload


CALCULATOR_REGISTRY: dict[str, "Calculator"] = {}


@dataclass
class Calculator:
    key: str
    consumes: list[str]
    func: Callable
    description: str = ""

    def __call__(self, facts: dict, tax_year: str) -> dict:
        return self.func(facts, tax_year)


def register(key: str, consumes: list[str], description: str = ""):
    """Decorator registering a calculator function under ``key``, declaring
    the TaxParameter keys it reads so impact analysis (Section 5.3) is a
    query over CALCULATOR_REGISTRY[key].consumes."""

    def decorator(func: Callable) -> Calculator:
        calc = Calculator(key=key, consumes=consumes, func=func, description=description)
        CALCULATOR_REGISTRY[key] = calc
        return calc

    return decorator


def calculators_consuming(parameter_key: str) -> list[str]:
    """Which calculators (and transitively, which strategies) are affected
    if this parameter changes — the mechanical query Section 5.3 promises."""
    return [c.key for c in CALCULATOR_REGISTRY.values() if parameter_key in c.consumes]


def _apply_band_rates(taxable: float, bands: list[dict]) -> tuple[float, list[dict]]:
    """Apply a sorted list of {"upper": float|None, "rate": float} bands to a
    taxable amount, splitting income into the each band as it fills up.
    ``upper`` is the cumulative upper bound of the band (None = no limit)."""
    tax = 0.0
    remaining = taxable
    lower = 0.0
    breakdown = []
    for band in bands:
        upper = band["upper"]
        band_size = (upper - lower) if upper is not None else remaining
        amount_in_band = max(0.0, min(remaining, band_size))
        band_tax = amount_in_band * band["rate"]
        tax += band_tax
        if amount_in_band > 0:
            breakdown.append(
                {"rate": band["rate"], "amount": round(amount_in_band, 2), "tax": round(band_tax, 2)}
            )
        remaining -= amount_in_band
        lower = upper if upper is not None else lower
        if remaining <= 0:
            break
    return round(tax, 2), breakdown
