"""Runs every GoldenTestCase row through its calculator (architecture doc
Section 5.5: "a release that changes any golden outcome without an
accompanying rule change is blocked"). This is the mechanical CI gate the
tax editor's golden test cases feed into; it is data-driven, not a fixed
list of asserts, so a new GoldenTestCase added via Admin is picked up
automatically.
"""

import pytest

from ruleengine.engine import CALCULATOR_REGISTRY
from ruleengine.models import GoldenTestCase


@pytest.fixture
def golden_cases(seeded_rule_base):
    return list(GoldenTestCase.objects.all())


def test_at_least_one_golden_case_seeded(golden_cases):
    assert len(golden_cases) > 0


def test_golden_cases_match_expected_output(golden_cases):
    failures = []
    for case in golden_cases:
        calculator = CALCULATOR_REGISTRY.get(case.calculator_key)
        if calculator is None:
            failures.append(f"{case}: no calculator registered for {case.calculator_key!r}")
            continue
        actual = calculator(case.input_facts, case.tax_year)
        for key, expected_value in case.expected_output.items():
            actual_value = actual.get(key)
            if isinstance(expected_value, (int, float)) and not isinstance(expected_value, bool):
                matches = actual_value == pytest.approx(expected_value)
            else:
                matches = actual_value == expected_value
            if not matches:
                failures.append(
                    f"{case}: field {key!r} expected {expected_value!r}, got {actual_value!r}"
                )
    assert not failures, "\n".join(failures)
