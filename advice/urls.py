from django.urls import path

from . import views

app_name = "advice"

urlpatterns = [
    path("generate/<int:fact_set_id>/review/", views.intake_review, name="intake-review"),
    path("generate/<int:fact_set_id>/", views.advice_generate, name="advice-generate"),
    path("<int:pk>/", views.advice_detail, name="advice-detail"),
    path("<int:pk>/panel/", views.panel_deploy, name="panel-deploy"),
    path("<int:pk>/decide/", views.advice_decide, name="advice-decide"),
    path("impact/", views.impact_alerts, name="impact-alerts"),
    path("impact/<int:pk>/review/", views.impact_alert_review, name="impact-alert-review"),
    path("scenario/<int:client_id>/", views.scenario, name="scenario"),
    path("<int:pk>/narrative/", views.narrative_draft, name="narrative-draft"),
    path("client/<int:client_id>/", views.advice_list, name="advice-list"),
]
