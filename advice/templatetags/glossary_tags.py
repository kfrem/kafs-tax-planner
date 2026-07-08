"""Template tags for the plain-English glossary drill-downs.

``{% explain "key" %}`` renders a term as a clickable drill-down trigger; the
popover content is driven client-side from the JSON that ``{% glossary_json %}``
emits once in the page shell.
"""

import json

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from advice import glossary

register = template.Library()


@register.simple_tag
def explain(key, label=None):
    """Render a term with a drill-down affordance. Falls back to plain text if
    the key is unknown, so it is always safe to use."""
    entry = glossary.get(key)
    text = label or (entry[0] if entry else key)
    if not entry:
        return text
    return format_html(
        '<span class="gloss" tabindex="0" role="button" data-gloss="{}" '
        'aria-label="Explain {}">{}<span class="gloss-i">i</span></span>',
        key, entry[0], text,
    )


@register.simple_tag
def glossary_json():
    """The whole glossary as JSON for the client-side popover script."""
    data = {
        k: {"term": v[0], "plain": v[1], "detail": v[2], "client": v[3]}
        for k, v in glossary.GLOSSARY.items()
    }
    return mark_safe(json.dumps(data))
