from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.queue, name="queue"),
    path("alert/<int:pk>/action/", views.alert_action, name="alert-action"),
]
