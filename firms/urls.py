from django.contrib.auth import views as auth_views
from django.urls import path

from . import mfa

app_name = "firms"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="firms/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("mfa/setup/", mfa.mfa_setup, name="mfa-setup"),
    path("mfa/verify/", mfa.mfa_verify, name="mfa-verify"),
]
