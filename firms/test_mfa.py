"""MFA (TOTP) tests: enrolment, enforcement for device holders, and that
users without a device are unaffected (rollout is per-user opt-in until a
firm mandates it operationally).
"""

import time

import pytest
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

pytestmark = pytest.mark.django_db


def _current_token(device: TOTPDevice) -> str:
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    return format(totp.token(), f"0{device.digits}d")


@pytest.fixture
def logged_in(client, staff_user):
    client.force_login(staff_user)
    return client


class TestEnrolment:
    def test_setup_page_shows_qr_and_confirms_with_token(self, logged_in, staff_user):
        response = logged_in.get("/accounts/mfa/setup/")
        assert response.status_code == 200
        assert b"data:image/png;base64," in response.content

        device = TOTPDevice.objects.get(user=staff_user, confirmed=False)
        response = logged_in.post("/accounts/mfa/setup/", {"token": _current_token(device)})
        assert response.status_code == 302
        device.refresh_from_db()
        assert device.confirmed is True

    def test_wrong_token_does_not_confirm(self, logged_in, staff_user):
        logged_in.get("/accounts/mfa/setup/")
        device = TOTPDevice.objects.get(user=staff_user, confirmed=False)
        logged_in.post("/accounts/mfa/setup/", {"token": "000000"})
        device.refresh_from_db()
        assert device.confirmed is False


class TestEnforcement:
    def test_no_device_means_no_prompt(self, logged_in):
        assert logged_in.get("/clients/").status_code == 200

    def test_device_holder_blocked_until_verified(self, client, staff_user):
        TOTPDevice.objects.create(user=staff_user, name="app", confirmed=True)
        client.force_login(staff_user)
        response = client.get("/clients/")
        assert response.status_code == 302
        assert response.url == "/accounts/mfa/verify/"

    def test_correct_token_unlocks_session(self, client, staff_user):
        device = TOTPDevice.objects.create(user=staff_user, name="app", confirmed=True)
        client.force_login(staff_user)
        response = client.post("/accounts/mfa/verify/", {"token": _current_token(device)})
        assert response.status_code == 302
        assert client.get("/clients/").status_code == 200

    def test_wrong_token_stays_locked(self, client, staff_user):
        TOTPDevice.objects.create(user=staff_user, name="app", confirmed=True)
        client.force_login(staff_user)
        client.post("/accounts/mfa/verify/", {"token": "000000"})
        assert client.get("/clients/").status_code == 302

    def test_logout_always_reachable(self, client, staff_user):
        TOTPDevice.objects.create(user=staff_user, name="app", confirmed=True)
        client.force_login(staff_user)
        assert client.post("/accounts/logout/").status_code in (200, 302)
