"""Branded PDF advice reports via WeasyPrint (architecture doc Section 3:
"Advice reports are generated as branded PDFs from the same templates as
the web views. Free, Python-native.").

The PDF is rendered on demand from the advice record (see advice.views.advice_pdf)
rather than served from disk: hosts with an ephemeral filesystem (e.g. Render's
free tier) do not persist written files across restarts, and Django does not
serve MEDIA in production. Rendering per download sidesteps both.
"""

from __future__ import annotations

from django.template.loader import render_to_string
from weasyprint import HTML


def advice_pdf_filename(advice_record) -> str:
    year = advice_record.tax_year.replace("/", "-")
    return f"advice_{advice_record.client_id}_{year}_{advice_record.pk}.pdf"


def advice_pdf_bytes(advice_record) -> bytes:
    """Render the branded advice report to PDF bytes (nothing written to disk)."""
    html_string = render_to_string("reports/advice_report.html", {"record": advice_record})
    return HTML(string=html_string).write_pdf()


def render_advice_pdf(advice_record) -> None:
    """Render and attach the PDF to the record (kept for callers that persist it;
    note the attachment is not durable on an ephemeral filesystem)."""
    advice_record.attach_rendered_report(advice_pdf_filename(advice_record), advice_pdf_bytes(advice_record))
