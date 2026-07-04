from django.db import connection


class FirmRowLevelSecurityMiddleware:
    """Sets a PostgreSQL session variable, ``app.current_firm_id``, on every
    request so the row-level security policies defined on client-data tables
    (see clients/migrations and advice/migrations) can enforce tenant
    isolation at the database layer, not only in application code
    (architecture doc Section 7.2).

    Superusers (vendor staff maintaining the rule base) bypass RLS entirely
    by setting the sentinel value ``ALL``. Unauthenticated or firmless
    requests get a sentinel that matches no real firm.
    """

    BYPASS_SENTINEL = "ALL"
    NONE_SENTINEL = "0"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user is not None and getattr(user, "is_authenticated", False):
            if user.is_superuser:
                value = self.BYPASS_SENTINEL
            elif user.firm_id:
                value = str(user.firm_id)
            else:
                value = self.NONE_SENTINEL
        else:
            value = self.NONE_SENTINEL

        with connection.cursor() as cursor:
            # Value is always our sentinel or an integer PK we control — not
            # user-supplied text — so string formatting here is safe.
            cursor.execute(f"SET app.current_firm_id = '{value}'")

        return self.get_response(request)
