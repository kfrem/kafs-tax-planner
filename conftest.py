import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

from firms.models import Firm

User = get_user_model()


@pytest.fixture(autouse=True)
def _default_rls_bypass(db):
    """RLS on client/advice tables (see firms/middleware.py) is normally
    satisfied by the request middleware. Tests that call model/service code
    directly, without going through a request, need the same session
    variable set — default to the superuser bypass sentinel so ordinary
    tests aren't tripped up by RLS; tests that specifically exercise RLS
    (firms/tests.py) override this within the test body."""
    with connection.cursor() as cursor:
        cursor.execute("SET app.current_firm_id = 'ALL'")
    yield


@pytest.fixture
def seeded_rule_base(db):
    call_command("seed_rule_base", "--release")


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm LLP", slug="test-firm-llp")


@pytest.fixture
def other_firm(db):
    return Firm.objects.create(name="Other Firm LLP", slug="other-firm-llp")


@pytest.fixture
def staff_user(db, firm):
    return User.objects.create_user(
        username="staffer", password="pw", firm=firm, role=User.Role.STAFF
    )


@pytest.fixture
def other_staff_user(db, other_firm):
    return User.objects.create_user(
        username="other-staffer", password="pw", firm=other_firm, role=User.Role.STAFF
    )


@pytest.fixture(autouse=True)
def _no_ssl_redirect_in_tests(settings):
    """CI runs with DEBUG=false, which enables the production
    SECURE_SSL_REDIRECT; the Django test client speaks plain HTTP, so
    every view test would see 301s. Security headers are exercised by
    `manage.py check --deploy` in CI instead."""
    settings.SECURE_SSL_REDIRECT = False
