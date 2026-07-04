from advice.generator import generate_advice
from clients.models import Client, ClientFactSet
from reports.pdf import render_advice_pdf
from reports.templatetags.report_format import quant_table


class TestQuantTableFilter:
    def test_money_percent_bool_and_labels(self):
        html = quant_table(
            {
                "corporation_tax": 17793.04,
                "salary": 12570,
                "effective_rate": 0.265,
                "fits_within_allowance": True,
                "ownership_months": 120,
                "recommendation": "remain_sole_trader",
            }
        )
        assert "£17,793.04" in html
        assert "£12,570" in html
        assert "26.5%" in html
        assert "<td>Yes</td>" in html
        assert "120" in html and "£120" not in html
        assert "Remain sole trader" in html
        assert "Corporation tax" in html  # humanised label

    def test_list_of_dicts_becomes_columned_table(self):
        html = quant_table(
            {
                "comparisons": [
                    {"salary": 0, "net_to_individual": 54000.31},
                    {"salary": 5000, "net_to_individual": 54017.50},
                ]
            }
        )
        assert html.count("<th") >= 3  # outer label + column headers
        assert "£54,017.50" in html

    def test_none_renders_as_dash(self):
        assert "—" in quant_table({"employer_route": None})


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
