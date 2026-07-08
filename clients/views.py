import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .csv_import import import_client_csv
from .forms import ClientFactSetForm, ClientForm, CsvImportForm
from .models import (
    Client,
    ClientAccess,
    ClientFactSet,
    accessible_clients,
    get_accessible_client_or_404,
)


@login_required
def client_list(request):
    clients = accessible_clients(request.user)
    return render(request, "clients/client_list.html", {"clients": clients})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.firm = request.user.firm
            client.created_by = request.user
            client.save()
            messages.success(request, f"Client '{client.name}' created.")
            return redirect("clients:client-detail", pk=client.pk)
    else:
        form = ClientForm()
    return render(request, "clients/client_form.html", {"form": form})


@login_required
def client_detail(request, pk):
    from .profile import client_profile

    client = get_accessible_client_or_404(request.user, pk)
    fact_sets = client.fact_sets.filter(superseded_by__isnull=True)
    latest = fact_sets.order_by("-created_at").first()
    profile = client_profile(latest.facts) if latest else None
    manages_access = request.user.role in ("partner", "manager") or request.user.is_superuser
    staff_users = []
    granted_ids = set()
    if manages_access:
        staff_users = list(
            get_user_model().objects.filter(firm=request.user.firm, role="staff")
        )
        granted_ids = set(
            client.access_grants.values_list("user_id", flat=True)
        )
    return render(
        request,
        "clients/client_detail.html",
        {
            "client": client,
            "fact_sets": fact_sets,
            "profile": profile,
            "manages_access": manages_access,
            "staff_users": staff_users,
            "granted_ids": granted_ids,
        },
    )


@login_required
def client_access(request, pk):
    """Partner/manager only: set which STAFF users may work on this client."""
    if not (request.user.role in ("partner", "manager") or request.user.is_superuser):
        messages.error(request, "Only partners and managers manage client access.")
        return redirect("clients:client-detail", pk=pk)
    client = get_object_or_404(Client, pk=pk, firm=request.user.firm)
    if request.method != "POST":
        return redirect("clients:client-detail", pk=pk)

    selected_ids = {int(uid) for uid in request.POST.getlist("staff")}
    staff = get_user_model().objects.filter(firm=request.user.firm, role="staff")
    for user in staff:
        if user.pk in selected_ids:
            ClientAccess.objects.get_or_create(
                client=client, user=user,
                defaults={"firm": request.user.firm, "granted_by": request.user},
            )
        else:
            ClientAccess.objects.filter(client=client, user=user).delete()
    messages.success(request, "Client access updated.")
    return redirect("clients:client-detail", pk=pk)


@login_required
def client_facts_create(request, pk):
    client = get_accessible_client_or_404(request.user, pk)
    if request.method == "POST":
        form = ClientFactSetForm(request.POST)
        if form.is_valid():
            existing = client.fact_sets.filter(
                tax_year=form.cleaned_data["tax_year"], superseded_by__isnull=True
            ).first()
            fact_set = ClientFactSet.objects.create(
                firm=request.user.firm,
                client=client,
                tax_year=form.cleaned_data["tax_year"],
                facts=form.to_facts(),
                source="manual",
                created_by=request.user,
            )
            if existing:
                existing.superseded_by = fact_set
                existing.save(update_fields=["superseded_by"])
            messages.success(request, f"Facts recorded for {client.name}, {fact_set.tax_year}.")
            return redirect("clients:client-detail", pk=client.pk)
    else:
        form = ClientFactSetForm()
    return render(request, "clients/client_facts_form.html", {"form": form, "client": client})


@login_required
def csv_import_view(request):
    result = None
    if request.method == "POST":
        form = CsvImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_client_csv(request.FILES["csv_file"], request.user.firm, request.user)
    else:
        form = CsvImportForm()
    return render(request, "clients/csv_import.html", {"form": form, "result": result})


# The columns the importer understands (see clients/csv_import.py). One example
# row is included so an accountant can see the expected format at a glance.
CSV_TEMPLATE_COLUMNS = [
    "client_reference", "client_name", "entity_type", "tax_year",
    "other_income", "salary_from_own_company", "dividends_from_own_company",
    "spouse_income", "company_profit_before_remuneration",
    "employment_allowance_available", "associated_companies",
    "sole_trade_annual_profit", "pension_threshold_income",
    "pension_adjusted_income", "pension_unused_aa_y1", "pension_unused_aa_y2",
    "pension_unused_aa_y3", "pension_desired_contribution",
]
CSV_TEMPLATE_EXAMPLE = {
    "client_reference": "C001", "client_name": "Jane Director",
    "entity_type": "individual_with_company", "tax_year": "2025/26",
    "salary_from_own_company": "12570", "dividends_from_own_company": "40000",
    "company_profit_before_remuneration": "120000",
}


@login_required
def csv_template_download(request):
    """Serve a ready-to-fill CSV template (headers + one example row)."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="uk-tax-planner-client-template.csv"'
    writer = csv.DictWriter(response, fieldnames=CSV_TEMPLATE_COLUMNS)
    writer.writeheader()
    writer.writerow({c: CSV_TEMPLATE_EXAMPLE.get(c, "0" if c not in
                     ("client_reference", "client_name", "entity_type", "tax_year") else "") for c in CSV_TEMPLATE_COLUMNS})
    return response
