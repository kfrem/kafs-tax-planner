from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .csv_import import import_client_csv
from .forms import ClientFactSetForm, ClientForm, CsvImportForm
from .models import Client, ClientAccess, ClientFactSet, accessible_clients, get_accessible_client_or_404


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
    client = get_accessible_client_or_404(request.user, pk)
    fact_sets = client.fact_sets.filter(superseded_by__isnull=True)
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
