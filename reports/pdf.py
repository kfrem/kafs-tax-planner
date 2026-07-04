"""Branded PDF advice reports via WeasyPrint (architecture doc Section 3:
"Advice reports are generated as branded PDFs from the same templates as
the web views. Free, Python-native.").
"""

from __future__ import annotations

from django.template.loader import render_to_string
from weasyprint import HTML


def render_advice_pdf(advice_record) -> None:
    html_string = render_to_string("reports/advice_report.html", {"record": advice_record})
    pdf_bytes = HTML(string=html_string).write_pdf()
    filename = f"advice_{advice_record.client_id}_{advice_record.tax_year.replace('/', '-')}_{advice_record.pk}.pdf"
    advice_record.attach_rendered_report(filename, pdf_bytes)
