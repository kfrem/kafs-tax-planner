import pytest

from advice.generator import NoReleasedRuleBaseError, generate_advice
from advice.models import AdviceRecord
from clients.models import Client, ClientFactSet


@pytest.fixture
def client_with_facts(db, firm, staff_user):
    client = Client.objects.create(
        firm=firm,
        reference="C001",
        name="Owner-Managed Ltd",
        entity_type=Client.EntityType.INDIVIDUAL_WITH_COMPANY,
        created_by=staff_user,
    )
    fact_set = ClientFactSet.objects.create(
        firm=firm,
        client=client,
        tax_year="2025/26",
        facts={
            "personal": {
                "other_income": 0,
                "salary_from_own_company": 0,
                "dividends_from_own_company": 0,
                "spouse_income": 15000,
            },
            "company": {
                "profit_before_remuneration": 100000,
                "employment_allowance_available": False,
                "associated_companies": 0,
            },
            "sole_trade": {"annual_profit": 0},
            "pension": {
                "threshold_income": 0,
                "adjusted_income": 0,
                "unused_aa_prior_3_years": [0, 0, 0],
                "desired_contribution": 10000,
            },
        },
        source="manual",
        created_by=staff_user,
    )
    return client, fact_set


def test_generate_advice_requires_released_rule_base(client_with_facts, staff_user):
    client, fact_set = client_with_facts
    with pytest.raises(NoReleasedRuleBaseError):
        generate_advice(client, fact_set, staff_user)


def test_generate_advice_runs_eligible_strategies(seeded_rule_base, client_with_facts, staff_user):
    client, fact_set = client_with_facts
    record = generate_advice(client, fact_set, staff_user)

    strategy_codes = {r["strategy_code"] for r in record.results}
    assert "salary-dividend-mix" in strategy_codes
    assert "pension-annual-allowance-carry-forward" in strategy_codes
    assert "marriage-allowance-transfer" in strategy_codes
    assert "incorporation-vs-sole-trade" not in strategy_codes  # no sole trade profit recorded

    assert record.input_data_hash
    assert record.rule_base_release is not None
    assert record.tax_year == "2025/26"


def test_advice_record_is_append_only(seeded_rule_base, client_with_facts, staff_user):
    client, fact_set = client_with_facts
    record = generate_advice(client, fact_set, staff_user)

    with pytest.raises(ValueError):
        record.results = []
        record.save()


def test_advice_record_cannot_be_deleted(seeded_rule_base, client_with_facts, staff_user):
    client, fact_set = client_with_facts
    record = generate_advice(client, fact_set, staff_user)

    with pytest.raises(ValueError):
        record.delete()

    assert AdviceRecord.objects.filter(pk=record.pk).exists()


def test_flagged_strategy_is_never_omitted(seeded_rule_base, client_with_facts, staff_user):
    client, fact_set = client_with_facts

    fact_set.facts["sole_trade"]["annual_profit"] = 80000
    fact_set.save()
    record = generate_advice(client, fact_set, staff_user)
    flagged = [r for r in record.results if r["strategy_code"] == "incorporation-vs-sole-trade"]
    assert flagged, "borderline-risk strategy must still appear when eligible, never silently dropped"
    assert flagged[0]["risk_status"] == "borderline"
