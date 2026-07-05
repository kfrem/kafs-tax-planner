"""Multi-factor authentication (architecture doc §7.2 "mandatory MFA"),
built on django-otp TOTP — works with any authenticator app, no paid
service anywhere.

Enforcement model: once a user has a CONFIRMED device, every request must
be OTP-verified — there is no way to skip the prompt or quietly disable
the device through the UI (removal is a support/admin operation, so a
stolen password alone can never turn MFA off).
"""

from __future__ import annotations

import base64
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django_otp import devices_for_user, login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice

EXEMPT_URL_NAMES = {"firms:mfa-verify", "firms:logout", "firms:login"}


class MfaEnforcementMiddleware:
    """Users with a confirmed TOTP device must verify it each session."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_verified()
            and TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()
            and request.resolver_match is None  # resolve lazily below
        ):
            pass
        if user is not None and user.is_authenticated and not user.is_verified():
            if TOTPDevice.objects.devices_for_user(user, confirmed=True).exists():
                path = request.path
                allowed = (
                    path == reverse("firms:mfa-verify")
                    or path == reverse("firms:logout")
                    or path.startswith("/static/")
                )
                if not allowed:
                    return redirect("firms:mfa-verify")
        return self.get_response(request)


def _qr_data_uri(text: str) -> str:
    image = qrcode.make(text)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


@login_required
def mfa_setup(request):
    confirmed = list(devices_for_user(request.user, confirmed=True))
    if confirmed:
        return render(request, "firms/mfa_setup.html", {"already_enabled": True})

    device, _ = TOTPDevice.objects.get_or_create(
        user=request.user, confirmed=False, defaults={"name": "Authenticator app"}
    )
    if request.method == "POST":
        token = request.POST.get("token", "").strip()
        if device.verify_token(token):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            otp_login(request, device)
            messages.success(
                request,
                "MFA enabled. From now on every login requires your authenticator code.",
            )
            return redirect("clients:client-list")
        messages.error(request, "That code did not match — scan the QR and try again.")

    return render(
        request,
        "firms/mfa_setup.html",
        {"qr_data_uri": _qr_data_uri(device.config_url), "already_enabled": False},
    )


@login_required
def mfa_verify(request):
    if request.method == "POST":
        token = request.POST.get("token", "").strip()
        for device in devices_for_user(request.user, confirmed=True):
            if device.verify_token(token):
                otp_login(request, device)
                messages.success(request, "Verified.")
                return redirect("clients:client-list")
        messages.error(request, "Invalid code.")
    return render(request, "firms/mfa_verify.html")
