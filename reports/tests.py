from advice.generator import generate_advice
from clients.models import Client, ClientFactSet
from reports.pdf import render_advice_pdf


def test_render_advice_pdf_attaches_file(seeded_rule_base, firm, staff_user):
    client = Client.objects.create(
        firm=firm,
        reference="C001",
        name="Report Test Ltd",
        entity_type=Client.EntityType.COMPANY,
        created_by=staff_user,
    )
    fact_set = ClientFactSet.objects.create(
        firm=firm,
        client=client,
        tax_year="2025/26",
        facts={"company": {"profit_before_remuneration": 80000}},
        source="manual",
        created_by=staff_user,
    )
    record = generate_advice(client, fact_set, staff_user)
    assert not record.rendered_report

    render_advice_pdf(record)
    record.refresh_from_db()

    assert record.rendered_report
    with record.rendered_report.open("rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"
