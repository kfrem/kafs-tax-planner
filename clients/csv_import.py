"""CSV import for client financial data (architecture doc Section 2:
"manual entry and spreadsheet import at MVP").

Expected header row (all numeric columns default to 0 if blank):

    client_reference, client_name, entity_type, tax_year, other_income,
    salary_from_own_company, dividends_from_own_company, spouse_income,
    company_profit_before_remuneration, employment_allowance_available,
    associated_companies, sole_trade_annual_profit,
    pension_threshold_income, pension_adjusted_income,
    pension_unused_aa_y1, pension_unused_aa_y2, pension_unused_aa_y3,
    pension_desired_contribution
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from .models import Client, ClientFactSet

REQUIRED_COLUMNS = {"client_reference", "client_name", "entity_type", "tax_year"}


@dataclass
class ImportResult:
    created_clients: int = 0
    updated_clients: int = 0
    created_fact_sets: int = 0
    errors: list[str] = field(default_factory=list)


def _num(row: dict, key: str) -> float:
    raw = (row.get(key) or "").strip()
    return float(raw) if raw else 0.0


def _bool(row: dict, key: str) -> bool:
    return (row.get(key) or "").strip().lower() in ("1", "true", "yes", "y")


def import_client_csv(file_obj, firm, user) -> ImportResult:
    result = ImportResult()
    text = file_obj.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        result.errors.append(f"Missing required column(s): {', '.join(sorted(missing))}")
        return result

    for line_number, row in enumerate(reader, start=2):
        reference = (row.get("client_reference") or "").strip()
        name = (row.get("client_name") or "").strip()
        entity_type = (row.get("entity_type") or "").strip()
        tax_year = (row.get("tax_year") or "").strip()

        if not (reference and name and entity_type and tax_year):
            result.errors.append(f"Row {line_number}: missing required value(s), skipped")
            continue
        if entity_type not in Client.EntityType.values:
            result.errors.append(
                f"Row {line_number}: invalid entity_type '{entity_type}', skipped"
            )
            continue

        client, created = Client.objects.update_or_create(
            firm=firm,
            reference=reference,
            defaults={"name": name, "entity_type": entity_type, "created_by": user},
        )
        if created:
            result.created_clients += 1
        else:
            result.updated_clients += 1

        facts = {
            "personal": {
                "other_income": _num(row, "other_income"),
                "salary_from_own_company": _num(row, "salary_from_own_company"),
                "dividends_from_own_company": _num(row, "dividends_from_own_company"),
                "spouse_income": _num(row, "spouse_income"),
            },
            "company": {
                "profit_before_remuneration": _num(row, "company_profit_before_remuneration"),
                "employment_allowance_available": _bool(row, "employment_allowance_available"),
                "associated_companies": int(_num(row, "associated_companies")),
            },
            "sole_trade": {"annual_profit": _num(row, "sole_trade_annual_profit")},
            "pension": {
                "threshold_income": _num(row, "pension_threshold_income"),
                "adjusted_income": _num(row, "pension_adjusted_income"),
                "unused_aa_prior_3_years": [
                    _num(row, "pension_unused_aa_y1"),
                    _num(row, "pension_unused_aa_y2"),
                    _num(row, "pension_unused_aa_y3"),
                ],
                "desired_contribution": _num(row, "pension_desired_contribution"),
            },
        }

        ClientFactSet.objects.create(
            firm=firm,
            client=client,
            tax_year=tax_year,
            facts=facts,
            source="csv_import",
            created_by=user,
        )
        result.created_fact_sets += 1

    return result
