"""Surface the count of unresolved editorial alerts in the chrome, so the
rule-base reviewer sees pending governance work from any page — not only
after navigating to the queue.

Staff-only and cheap: the query runs a single COUNT and only for
authenticated staff (the tax editor / reviewer). For everyone else it is
a no-op returning zero, so no query is issued on firm-user or anonymous
requests."""

from .models import ChangeAlert

OPEN_STATUSES = (ChangeAlert.Status.NEW, ChangeAlert.Status.UNDER_REVIEW)


def open_alert_count(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not user.is_staff:
        return {"open_alert_count": 0}
    return {
        "open_alert_count": ChangeAlert.objects.filter(status__in=OPEN_STATUSES).count()
    }
