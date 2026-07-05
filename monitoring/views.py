"""Editorial queue views. Staff-only (tax editor / reviewer): this is
rule-base governance, not firm workspace."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from authority.models import Authority, record_status_change
from ruleengine.models import RuleBaseRelease

from .models import ChangeAlert, WatchedSource


@staff_member_required
def queue(request):
    alerts = ChangeAlert.objects.select_related("source", "source__authority", "reviewed_by")
    open_alerts = [a for a in alerts if a.status in ("new", "under_review")]
    closed_alerts = [a for a in alerts if a.status in ("actioned", "dismissed")][:25]
    sources = WatchedSource.objects.all()
    return render(
        request,
        "monitoring/queue.html",
        {
            "open_alerts": open_alerts,
            "closed_alerts": closed_alerts,
            "sources": sources,
            "releases": RuleBaseRelease.objects.order_by("-effective_date", "-id"),
        },
    )


@staff_member_required
def alert_action(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    alert = get_object_or_404(ChangeAlert, pk=pk)
    action = request.POST.get("action", "")
    notes = request.POST.get("notes", "")
    try:
        if action == "under_review":
            alert.mark_under_review(request.user)
        elif action in (ChangeAlert.Status.ACTIONED, ChangeAlert.Status.DISMISSED):
            release = None
            if request.POST.get("release"):
                release = get_object_or_404(RuleBaseRelease, pk=request.POST["release"])
            alert.resolve(request.user, action, notes, release=release)
        else:
            messages.error(request, "Unknown action.")
            return redirect("monitoring:queue")
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Alert updated: {alert.get_status_display()}.")
    return redirect("monitoring:queue")
