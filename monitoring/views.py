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
def authorities(request):
    """Case-law/status workflow: every authority with its live status,
    dependent strategies (blast radius), and the append-only change log."""
    rows = []
    for authority in Authority.objects.prefetch_related("strategies", "status_changes"):
        rows.append(
            {
                "authority": authority,
                "strategies": list(authority.strategies.all()),
                "last_change": authority.status_changes.first(),
            }
        )
    return render(
        request,
        "monitoring/authorities.html",
        {"rows": rows, "statuses": Authority.Status.choices},
    )


@staff_member_required
def authority_status(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    authority = get_object_or_404(Authority, pk=pk)
    try:
        change = record_status_change(
            authority, request.user, request.POST.get("new_status", ""), request.POST.get("reason", "")
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("monitoring:authorities")

    # Surface the follow-up in the editorial queue so dependent-strategy
    # review is tracked to a resolution, like any detected change.
    watched = authority.watched_sources.first()
    if watched is not None:
        ChangeAlert.objects.create(
            source=watched,
            previous_fingerprint=f"status:{change.old_status}",
            new_fingerprint=f"status:{change.new_status}",
            diff_excerpt=(
                f"Authority status changed {change.old_status} -> {change.new_status} "
                f"by {request.user}.\nReason: {change.reason}\n"
                "Review every dependent strategy's risk classification."
            ),
        )
    dependents = authority.strategies.count()
    messages.success(
        request,
        f"{authority.canonical_citation} marked {change.new_status}; "
        f"{dependents} dependent strateg{'y' if dependents == 1 else 'ies'} flagged for review.",
    )
    return redirect("monitoring:authorities")


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
