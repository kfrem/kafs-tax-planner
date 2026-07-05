"""Per-client access controls: partners/managers see the whole firm's
clients; STAFF users see only clients granted to them — enforced in every
client-touching view, on top of the firm-level row-level security.
"""

import pytest
from django.contrib.auth import get_user_model

from clients.models import Client, ClientAccess, accessible_clients

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def partner(firm):
    return User.objects.create_user(username="partner1", password="pw", firm=firm, role=User.Role.PARTNER)


@pytest.fixture
def two_clients(firm, partner):
    a = Client.objects.create(firm=firm, reference="A1", name="Client A",
                              entity_type="individual", created_by=partner)
    b = Client.objects.create(firm=firm, reference="B1", name="Client B",
                              entity_type="individual", created_by=partner)
    return a, b


class TestAccessRules:
    def test_partner_sees_all_staff_sees_granted_only(self, firm, partner, staff_user, two_clients):
        client_a, client_b = two_clients
        ClientAccess.objects.create(firm=firm, client=client_a, user=staff_user, granted_by=partner)

        assert set(accessible_clients(partner)) == {client_a, client_b}
        assert set(accessible_clients(staff_user)) == {client_a}

    def test_staff_detail_view_404s_without_grant(self, client, firm, partner, staff_user, two_clients):
        client_a, client_b = two_clients
        ClientAccess.objects.create(firm=firm, client=client_a, user=staff_user, granted_by=partner)
        client.force_login(staff_user)

        assert client.get(f"/clients/{client_a.pk}/").status_code == 200
        assert client.get(f"/clients/{client_b.pk}/").status_code == 404
        # Advice-side views enforce the same boundary.
        assert client.get(f"/advice/client/{client_b.pk}/").status_code == 404
        assert client.get(f"/advice/scenario/{client_b.pk}/").status_code == 404

    def test_partner_manages_grants_via_view(self, client, firm, partner, staff_user, two_clients):
        client_a, _ = two_clients
        client.force_login(partner)
        response = client.post(f"/clients/{client_a.pk}/access/", {"staff": [str(staff_user.pk)]})
        assert response.status_code == 302
        assert ClientAccess.objects.filter(client=client_a, user=staff_user).exists()

        # Unticking revokes.
        client.post(f"/clients/{client_a.pk}/access/", {})
        assert not ClientAccess.objects.filter(client=client_a, user=staff_user).exists()

    def test_staff_cannot_manage_grants(self, client, firm, staff_user, two_clients):
        client_a, _ = two_clients
        client.force_login(staff_user)
        response = client.post(f"/clients/{client_a.pk}/access/", {"staff": [str(staff_user.pk)]})
        assert response.status_code == 302  # redirected away with error
        assert not ClientAccess.objects.filter(client=client_a, user=staff_user).exists()
