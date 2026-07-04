"""UK tax year helpers.

The UK income tax / CT / IHT year runs 6 April to 5 April. Calculators are
always given a tax year label (e.g. "2025/26"), not a wall-clock date, so
that "what did the tool believe on 12 March 2027?" (Section 5.5) is answered
by which tax year the advice was for, not by when it happens to be run.
"""

from __future__ import annotations

import datetime
import re

TAX_YEAR_RE = re.compile(r"^(\d{4})/(\d{2})$")


def parse_tax_year(tax_year: str) -> int:
    """Return the calendar year in which the tax year starts, e.g. '2025/26' -> 2025."""
    match = TAX_YEAR_RE.match(tax_year)
    if not match:
        raise ValueError(f"Invalid tax year label: {tax_year!r}, expected e.g. '2025/26'")
    start_year = int(match.group(1))
    end_suffix = match.group(2)
    if int(str(start_year + 1)[-2:]) != int(end_suffix):
        raise ValueError(f"Tax year label {tax_year!r} is not a consecutive year pair")
    return start_year


def anchor_date(tax_year: str) -> datetime.date:
    """A date guaranteed to fall inside the given tax year — used to look up
    which effective-dated rule applies. 6 April is the first day."""
    start_year = parse_tax_year(tax_year)
    return datetime.date(start_year, 4, 6)


def tax_year_bounds(tax_year: str) -> tuple[datetime.date, datetime.date]:
    start_year = parse_tax_year(tax_year)
    return datetime.date(start_year, 4, 6), datetime.date(start_year + 1, 4, 5)


def tax_year_for_date(date: datetime.date) -> str:
    if date >= datetime.date(date.year, 4, 6):
        start_year = date.year
    else:
        start_year = date.year - 1
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def previous_tax_years(tax_year: str, count: int) -> list[str]:
    start_year = parse_tax_year(tax_year)
    return [f"{y}/{str(y + 1)[-2:]}" for y in range(start_year - count, start_year)]
