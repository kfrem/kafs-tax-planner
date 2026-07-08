"""The plain-English glossary and its drill-down template tag."""

import json

from django.template import engines

from advice import glossary


def test_every_entry_has_all_four_layers():
    for key, entry in glossary.GLOSSARY.items():
        assert len(entry) == 4, key
        term, plain, detail, client = entry
        assert term and plain and detail  # client line may be an internal note but present
        assert isinstance(client, str)


def test_all_terms_sorted_and_complete():
    terms = glossary.all_terms()
    assert len(terms) == len(glossary.GLOSSARY)
    labels = [t["term"].lower() for t in terms]
    assert labels == sorted(labels)


def test_explain_tag_renders_drilldown_and_falls_back():
    dj = engines["django"]
    html = dj.from_string('{% load glossary_tags %}{% explain "expert_panel" "Panel" %}').render({})
    assert 'class="gloss"' in html and 'data-gloss="expert_panel"' in html and "Panel" in html
    # unknown key falls back to plain text, never errors
    plain = dj.from_string('{% load glossary_tags %}{% explain "no_such_key" "Word" %}').render({})
    assert plain.strip() == "Word"


def test_glossary_json_is_valid_and_complete():
    dj = engines["django"]
    raw = dj.from_string("{% load glossary_tags %}{% glossary_json %}").render({})
    data = json.loads(raw)
    assert set(data) == set(glossary.GLOSSARY)
    assert set(data["blocker"]) == {"term", "plain", "detail", "client"}
