"""Accountant-grade rendering of strategy quantification payloads.

The engine emits nested dicts/lists of plain values; these filters turn
them into readable tables: £-formatted money, percentages for rates,
humanised labels, Yes/No booleans. Pure presentation — the underlying
JSON in the advice record is untouched and remains the audit source.
"""

from __future__ import annotations

from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

# Keys whose numeric values are NOT money.
_PLAIN_HINTS = ("months", "years", "count", "options", "_id", "number_of")
# Keys whose numeric values are proportions -> render as percentages.
_PERCENT_HINTS = ("rate", "fraction", "reduction", "ratio")


def _label(key) -> str:
    text = str(key).replace("_", " ").strip()
    return text[:1].upper() + text[1:]


def _format_scalar(key, value) -> str:
    key_l = str(key).lower()
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        if any(h in key_l for h in _PERCENT_HINTS) and abs(value) <= 1:
            return f"{value * 100:.4g}%"
        if any(h in key_l for h in _PLAIN_HINTS):
            return f"{value:,.0f}" if float(value).is_integer() else f"{value:,}"
        if float(value).is_integer():
            return f"£{value:,.0f}"
        return f"£{value:,.2f}"
    if isinstance(value, str):
        return _label(value)
    return str(value)


def _render(key, value) -> str:
    if isinstance(value, dict):
        rows = format_html_join(
            "",
            '<tr><th style="text-align:left; white-space:nowrap;">{}</th><td>{}</td></tr>',
            ((_label(k), mark_safe(_render(k, v))) for k, v in value.items()),
        )
        return format_html('<table class="quant">{}</table>', rows)
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            columns = list(value[0].keys())
            head = format_html_join(
                "", "<th>{}</th>", ((_label(c),) for c in columns)
            )
            body = format_html_join(
                "",
                "<tr>{}</tr>",
                (
                    (
                        format_html_join(
                            "",
                            '<td style="text-align:right;">{}</td>',
                            ((mark_safe(_render(c, item.get(c))),) for c in columns),
                        ),
                    )
                    for item in value
                ),
            )
            return format_html(
                '<table class="quant"><tr>{}</tr>{}</table>', head, body
            )
        return ", ".join(_format_scalar(key, item) for item in value)
    return _format_scalar(key, value)


@register.filter
def quant_table(quantification):
    """Render a strategy quantification dict as nested HTML tables."""
    if not isinstance(quantification, dict):
        return _format_scalar("", quantification)
    return mark_safe(_render("", quantification))
