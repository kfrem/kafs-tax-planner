from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .csv_import import import_client_csv
from .forms import ClientFactSetForm, ClientForm, CsvImportForm
from .models import Client, ClientFactSet


@login_required
def client_list(request):
    clients = Client.objects.filter(firm=request.user.firm, is_active=True)
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
    client = get_object_or_404(Client, pk=pk, firm=request.user.firm)
    fact_sets = client.fact_sets.filter(superseded_by__isnull=True)
    return render(
        request, "clients/client_detail.html", {"client": client, "fact_sets": fact_sets}
    )


@login_required
def client_facts_create(request, pk):
    client = get_object_or_404(Client, pk=pk, firm=request.user.firm)
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
