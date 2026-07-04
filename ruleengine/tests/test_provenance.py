"""Rule-provenance and draft-gating tests: closes the audit-integrity gap
found during the simulated-Budget demonstration, where an advice record's
release stamp did not identify the parameter rows actually read.
"""

import datetime

import pytest
from psycopg.types.range import Range

from ruleengine.engine import (
    RuleNotFoundError,
    get_parameter,
    parameter_provenance,
)
from ruleengine.models import RuleBaseRelease, TaxParameter

pytestmark = [pytest.mark.usefixtures("seeded_rule_base"), pytest.mark.django_db]

TAX_YEAR = "2025/26"


def _staged_row(status):
    release = RuleBaseRelease.objects.create(
        version=f"9999.test-{status}",
        changelog="test staging",
        effective_date=datetime.date(2025, 4, 6),
        status=status,
        editor=RuleBaseRelease.objects.first().editor,
    )
    # Newer row id for the same key/period: without status gating this row
    # would win the order_by("-id") tie-break.
    row = TaxParameter.objects.create(
        key="income_tax.personal_allowance",
        label="STAGED personal allowance",
        tax_domain="personal_income_tax",
        effective_range=Range(datetime.date(2025, 4, 6), None, bounds="[)"),
        payload={"amount": 99999, "taper_threshold": 100000, "taper_rate": 0.5},
        risk_classification="settled",
        introduced_in_release=release,
    )
    return release, row


class TestDraftGating:
    def test_draft_release_rows_never_influence_calculations(self):
        _staged_row(RuleBaseRelease.Status.DRAFT)
        payload = get_parameter("income_tax.personal_allowance", TAX_YEAR)
        assert payload["amount"] == 12570  # the released row, not the draft

    def test_released_rows_do_take_effect(self):
        _staged_row(RuleBaseRelease.Status.RELEASED)
        payload = get_parameter("income_tax.personal_allowance", TAX_YEAR)
        assert payload["amount"] == 99999

    def test_no_released_row_raises(self):
        TaxParameter.objects.filter(key="income_tax.personal_allowance").update(
            introduced_in_release=_staged_row(RuleBaseRelease.Status.DRAFT)[0]
        )
        with pytest.raises(RuleNotFoundError):
            get_parameter("income_tax.personal_allowance", TAX_YEAR)


class TestProvenance:
    def test_log_records_exact_rows_read(self):
        with parameter_provenance() as log:
            get_parameter("income_tax.personal_allowance", TAX_YEAR)
            get_parameter("iht.nil_rate_band", TAX_YEAR)
        entries = {m["key"]: m for m in log.values()}
        assert set(entries) == {"income_tax.personal_allowance", "iht.nil_rate_band"}
        pa = entries["income_tax.personal_allowance"]
        row = TaxParameter.objects.get(pk=pa["parameter_id"])
        assert row.payload["amount"] == 12570
        assert pa["release"] == row.introduced_in_release.version
        assert pa["effective_from"] == "2025-04-06"

    def test_provenance_survives_parameter_cache_hits(self):
        from ruleengine.engine import parameter_cache

        with parameter_provenance() as log:
            with parameter_cache():
                get_parameter("iht.rates", TAX_YEAR)
                get_parameter("iht.rates", TAX_YEAR)  # cache hit must still log
        assert [m["key"] for m in log.values()] == ["iht.rates"]
