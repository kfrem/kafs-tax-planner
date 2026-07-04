import io

from clients.csv_import import import_client_csv
from clients.models import Client, ClientFactSet

CSV_HEADER = (
    "client_reference,client_name,entity_type,tax_year,other_income,"
    "salary_from_own_company,dividends_from_own_company,spouse_income,"
    "company_profit_before_remuneration,employment_allowance_available,"
    "associated_companies,sole_trade_annual_profit,pension_threshold_income,"
    "pension_adjusted_income,pension_unused_aa_y1,pension_unused_aa_y2,"
    "pension_unused_aa_y3,pension_desired_contribution\n"
)


def _csv_file(rows: list[str]):
    content = CSV_HEADER + "\n".join(rows)
    return io.BytesIO(content.encode("utf-8"))


def test_import_creates_client_and_fact_set(db, firm, staff_user):
    row = "C001,Acme Ltd,company,2025/26,0,50000,20000,0,150000,false,0,0,0,0,0,0,0,0"
    result = import_client_csv(_csv_file([row]), firm, staff_user)

    assert result.created_clients == 1
    assert result.created_fact_sets == 1
    assert not result.errors

    client = Client.objects.get(firm=firm, reference="C001")
    fact_set = ClientFactSet.objects.get(client=client)
    assert fact_set.facts["personal"]["salary_from_own_company"] == 50000
    assert fact_set.facts["company"]["profit_before_remuneration"] == 150000


def test_import_rejects_missing_required_columns():
    bad_file = io.BytesIO(b"client_reference,client_name\nC1,Acme\n")
    result = import_client_csv(bad_file, firm=None, user=None)
    assert result.errors
    assert result.created_clients == 0


def test_import_skips_invalid_entity_type(db, firm, staff_user):
    row = "C002,Bad Ltd,not_a_type,2025/26,0,0,0,0,0,false,0,0,0,0,0,0,0,0"
    result = import_client_csv(_csv_file([row]), firm, staff_user)
    assert result.created_clients == 0
    assert any("invalid entity_type" in e for e in result.errors)


def test_reimporting_same_reference_updates_not_duplicates(db, firm, staff_user):
    row = "C001,Acme Ltd,company,2025/26,0,0,0,0,100000,false,0,0,0,0,0,0,0,0"
    import_client_csv(_csv_file([row]), firm, staff_user)
    result = import_client_csv(_csv_file([row]), firm, staff_user)

    assert result.updated_clients == 1
    assert result.created_clients == 0
    assert Client.objects.filter(firm=firm).count() == 1
