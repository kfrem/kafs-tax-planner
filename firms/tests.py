"""Row-level security is enforced by PostgreSQL itself (architecture doc
Section 7.2), not only by the firm=... filters in views. These tests set
the same session variable FirmRowLevelSecurityMiddleware sets, without
going through a request, to prove the database-level policy holds even if
application code forgets a filter.
"""

from django.db import connection

from clients.models import Client


def _set_firm_context(value: str):
    with connection.cursor() as cursor:
        cursor.execute(f"SET app.current_firm_id = '{value}'")


def test_firm_cannot_see_other_firms_clients(db, firm, other_firm, staff_user, other_staff_user):
    Client.objects.create(
        firm=firm, reference="A1", name="Alpha Ltd", entity_type="company", created_by=staff_user
    )
    Client.objects.create(
        firm=other_firm,
        reference="B1",
        name="Beta Ltd",
        entity_type="company",
        created_by=other_staff_user,
    )

    _set_firm_context(str(firm.id))
    visible = list(Client.objects.all())
    assert [c.name for c in visible] == ["Alpha Ltd"]

    _set_firm_context(str(other_firm.id))
    visible = list(Client.objects.all())
    assert [c.name for c in visible] == ["Beta Ltd"]


def test_superuser_bypass_sees_all_firms(db, firm, other_firm, staff_user, other_staff_user):
    Client.objects.create(
        firm=firm, reference="A1", name="Alpha Ltd", entity_type="company", created_by=staff_user
    )
    Client.objects.create(
        firm=other_firm,
        reference="B1",
        name="Beta Ltd",
        entity_type="company",
        created_by=other_staff_user,
    )

    _set_firm_context("ALL")
    assert Client.objects.count() == 2


def test_no_firm_context_sees_nothing(db, firm, staff_user):
    Client.objects.create(
        firm=firm, reference="A1", name="Alpha Ltd", entity_type="company", created_by=staff_user
    )
    _set_firm_context("0")
    assert Client.objects.count() == 0


def test_healthz_is_public_and_reports_ok(client, db):
    # Load balancers probe /healthz unauthenticated; it must return 200 and
    # confirm database reachability without redirecting to login or touching
    # client data.
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
