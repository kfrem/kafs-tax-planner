from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client-list"),
    path("new/", views.client_create, name="client-create"),
    path("import/", views.csv_import_view, name="csv-import"),
    path("import/template/", views.csv_template_download, name="csv-template"),
    path("<int:pk>/", views.client_detail, name="client-detail"),
    path("<int:pk>/facts/new/", views.client_facts_create, name="client-facts-create"),
    path("<int:pk>/access/", views.client_access, name="client-access"),
]
