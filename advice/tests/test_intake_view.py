"""The pre-generation intake review page: before generating advice, the
accountant sees the questions the engine would otherwise assume for this fact
set, then proceeds to generate.
"""

import pytest
from django.urls import reverse

from clients.models import Client, ClientFactSet

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


def _fact_set(firm, user, facts):
    client = Client.objects.create(
        firm=firm, reference="R1", name="Review Client",
        entity_type="individual", created_by=user,
    )
    return ClientFactSet.objects.create(
        firm=firm, client=client, tax_year="2025/26", facts=facts,
        source="manual", created_by=user,
    )


def test_review_page_lists_the_intake_questions(client, firm, staff_user):
    # A landlord fact set with no jurisdiction and no marital status recorded:
    # the review page must surface those questions before generation.
    fact_set = _fact_set(firm, staff_user, {"property": {"rental_income": 24000}})
    client.force_login(staff_user)
    resp = client.get(reverse("advice:intake-review", args=[fact_set.pk]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Questions to confirm first" in body
    assert "married or in a civil partnership" in body  # marital status question
    assert "mortgaged" in body                           # landlord s.24 question


def test_fully_recorded_facts_show_no_questions(client, firm, staff_user):
    fact_set = _fact_set(firm, staff_user, {"personal": {"spouse_income": 30000}})
    client.force_login(staff_user)
    resp = client.get(reverse("advice:intake-review", args=[fact_set.pk]))
    assert resp.status_code == 200
    assert "No material assumptions" in resp.content.decode()
