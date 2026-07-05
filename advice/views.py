from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from clients.models import Client, ClientFactSet
from reports.pdf import render_advice_pdf

from .generator import NoReleasedRuleBaseError, generate_advice
from .models import AdviceImpactAlert, AdviceRecord, ProfessionalDecision
from .panel import DecisionError, deploy_panel, record_decision


@login_required
def advice_generate(request, fact_set_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    fact_set = get_object_or_404(ClientFactSet, pk=fact_set_id, firm=request.user.firm)
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
    return render(request, "advice/advice_detail.html", {"record": record})


@login_required
def panel_deploy(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    record = get_object_or_404(AdviceRecord, pk=pk, firm=request.user.firm)
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
    client = get_object_or_404(Client, pk=client_id, firm=request.user.firm)
    records = client.advice_records.all()
    return render(request, "advice/advice_list.html", {"client": client, "records": records})
