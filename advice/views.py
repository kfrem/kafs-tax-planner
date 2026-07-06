from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from clients.models import (
    ClientFactSet,
    get_accessible_client_or_404,
)
from reports.pdf import render_advice_pdf

from .generator import NoReleasedRuleBaseError, generate_advice
from .intake import intake_gaps
from .models import AdviceImpactAlert, AdviceRecord, ProfessionalDecision
from .narrative import NarrativeRejected, create_narrative
from .panel import DecisionError, deploy_panel, persona_summaries, record_decision
from .scenarios import run_scenario


@login_required
def advice_generate(request, fact_set_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    fact_set = get_object_or_404(ClientFactSet, pk=fact_set_id, firm=request.user.firm)
    get_accessible_client_or_404(request.user, fact_set.client_id)
    try:
        record = generate_advice(fact_set.client, fact_set, request.user)
    except NoReleasedRuleBaseError:
        messages.error(
            request,
            "No released rule-base version is currently in force. "
            "A tax editor must approve a release before advice can be generated.",
        )
        return redirect("clients:client-detail", pk=fact_set.client_id)

    render_advice_pdf(record)
    messages.success(request, "Advice generated.")
    return redirect("advice:advice-detail", pk=record.pk)


@login_required
def advice_detail(request, pk):
    record = get_object_or_404(AdviceRecord, pk=pk, firm=request.user.firm)
    get_accessible_client_or_404(request.user, record.client_id)
    review = record.latest_panel_review
    return render(
        request,
        "advice/advice_detail.html",
        {
            "record": record,
            "panel_summaries": persona_summaries(review) if review else None,
            "narrative": record.narratives.order_by("-created_at").first(),
            "intake_gaps": intake_gaps(record.input_data_snapshot),
        },
    )


@login_required
def narrative_draft(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    record = get_object_or_404(AdviceRecord, pk=pk, firm=request.user.firm)
    get_accessible_client_or_404(request.user, record.client_id)
    try:
        create_narrative(record, request.user)
    except NarrativeRejected as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            "Narrative drafted and validated: every figure and citation checked "
            "against the advice record. Edit before issuing to the client.",
        )
    return redirect("advice:advice-detail", pk=record.pk)


@login_required
def panel_deploy(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    record = get_object_or_404(AdviceRecord, pk=pk, firm=request.user.firm)
    get_accessible_client_or_404(request.user, record.client_id)
    review = deploy_panel(record, request.user)
    messages.success(
        request,
        f"Expert panel deployed: {len(review.findings)} findings, "
        f"overall verdict '{review.verdicts['overall']}'.",
    )
    return redirect("advice:advice-detail", pk=record.pk)


@login_required
def advice_decide(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    record = get_object_or_404(AdviceRecord, pk=pk, firm=request.user.firm)
    get_accessible_client_or_404(request.user, record.client_id)
    decision = request.POST.get("decision", "")
    if decision not in ProfessionalDecision.Decision.values:
        messages.error(request, "Choose approve, reject, or needs revision.")
        return redirect("advice:advice-detail", pk=record.pk)
    try:
        record_decision(record, request.user, decision, request.POST.get("notes", ""))
    except DecisionError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Decision recorded: {decision.replace('_', ' ')}.")
    return redirect("advice:advice-detail", pk=record.pk)


class ScenarioForm(forms.Form):
    """Optional overrides; only supplied values change the scenario facts."""

    OVERRIDE_PATHS = {
        "company_profit": "company.profit_before_remuneration",
        "sole_trade_profit": "sole_trade.annual_profit",
        "employment_income": "personal.employment_income",
        "other_income": "personal.other_income",
        "pension_contribution": "pension.desired_contribution",
        "planned_gift": "estate.planned_lifetime_gift",
        "disposal_gain": "property.disposal_gain",
    }

    company_profit = forms.FloatField(required=False, min_value=0)
    sole_trade_profit = forms.FloatField(required=False, min_value=0)
    employment_income = forms.FloatField(required=False, min_value=0)
    other_income = forms.FloatField(required=False, min_value=0)
    pension_contribution = forms.FloatField(required=False, min_value=0)
    planned_gift = forms.FloatField(required=False, min_value=0)
    disposal_gain = forms.FloatField(required=False, min_value=0)

    def overrides(self):
        return {
            self.OVERRIDE_PATHS[name]: value
            for name, value in self.cleaned_data.items()
            if value is not None
        }


@login_required
def scenario(request, client_id):
    client = get_accessible_client_or_404(request.user, client_id)
    fact_set = (
        client.fact_sets.filter(superseded_by__isnull=True).order_by("-created_at").first()
    )
    if fact_set is None:
        messages.error(request, "Record facts for this client before modelling scenarios.")
        return redirect("clients:client-detail", pk=client.pk)

    result = None
    form = ScenarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        overrides = form.overrides()
        if overrides:
            result = run_scenario(fact_set.facts, fact_set.tax_year, overrides)
        else:
            messages.error(request, "Change at least one value to model a scenario.")
    return render(
        request,
        "advice/scenario.html",
        {"client": client, "fact_set": fact_set, "form": form, "result": result},
    )


@login_required
def impact_alerts(request):
    alerts = AdviceImpactAlert.objects.filter(firm=request.user.firm).select_related(
        "advice_record__client", "release", "reviewed_by"
    )
    return render(
        request,
        "advice/impact_alerts.html",
        {
            "open_alerts": [a for a in alerts if a.status == "open"],
            "reviewed_alerts": [a for a in alerts if a.status == "reviewed"][:25],
        },
    )


@login_required
def impact_alert_review(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    alert = get_object_or_404(AdviceImpactAlert, pk=pk, firm=request.user.firm)
    alert.mark_reviewed(request.user, request.POST.get("note", ""))
    messages.success(request, "Impact alert marked reviewed.")
    return redirect("advice:impact-alerts")


@login_required
def advice_list(request, client_id):
    client = get_accessible_client_or_404(request.user, client_id)
    records = client.advice_records.all()
    return render(request, "advice/advice_list.html", {"client": client, "records": records})
