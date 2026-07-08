"""The LLM narrative drafter: safe when unconfigured, and bound by the same
validator so it can never introduce an ungrounded number."""

import pytest

from advice import narrative_llm
from advice.narrative import NarrativeRejected, validate_narrative


def test_llm_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert narrative_llm.llm_available() is False


def test_llm_available_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert narrative_llm.llm_available() is True


def test_llm_draft_raises_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    class _Rec:
        pass

    with pytest.raises(RuntimeError):
        narrative_llm.llm_draft(_Rec())


class _FakeRecord:
    """Minimal record shape for the validator: one strategy with a £5,000 figure."""

    tax_year = "2025/26"

    class _Client:
        name = "Test"

    client = _Client()
    results = [{
        "strategy_name": "Pension contribution",
        "explanation": "A contribution attracts relief.",
        "quantification": {"saving": 5000.0},
        "authorities": [{"citation": "Finance Act 2004 s.190"}],
    }]


def test_validator_rejects_an_llm_hallucinated_number():
    # Simulate an LLM draft that invents a figure not in the record.
    bad = "Dear Test, this plan saves you £9,999 through a pension contribution."
    report = validate_narrative(bad, _FakeRecord())
    assert report["valid"] is False
    assert any("9,999" in v for v in report["violations"])


def test_validator_accepts_a_grounded_draft():
    good = "Dear Test, a pension contribution could save £5,000 (Finance Act 2004 s.190)."
    report = validate_narrative(good, _FakeRecord())
    assert report["valid"] is True
