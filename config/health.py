"""Liveness/readiness probe for load balancers and container orchestration.

Unauthenticated by design (probes carry no credentials) and side-effect
free: it runs a trivial ``SELECT 1`` so an app that is up but cannot reach
its database reports unhealthy (503) and is taken out of rotation, rather
than serving errors. No client data is touched and nothing is leaked.
"""

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache


@never_cache
def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unhealthy", "database": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"}, status=200)
