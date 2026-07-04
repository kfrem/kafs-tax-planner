"""Enforce multi-tenant isolation in the database itself (architecture doc
Section 7.2), not only via the firm=request.user.firm filters already
applied in clients/views.py. FirmRowLevelSecurityMiddleware sets the
`app.current_firm_id` session variable on every request; superusers get
the sentinel 'ALL' and bypass isolation entirely.

FORCE ROW LEVEL SECURITY is required because, by default, PostgreSQL
exempts the table owner (our app_user role) from its own RLS policies.
"""

from django.db import migrations

TABLES = ["clients_client", "clients_clientfactset"]

RLS_SQL = """
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
CREATE POLICY firm_isolation ON {table}
    USING (
        CASE current_setting('app.current_firm_id', true)
            WHEN 'ALL' THEN true
            ELSE firm_id = NULLIF(current_setting('app.current_firm_id', true), '')::bigint
        END
    );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS firm_isolation ON {table};
ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0002_initial"),
    ]

    operations = [
        migrations.RunSQL(RLS_SQL.format(table=t), REVERSE_SQL.format(table=t)) for t in TABLES
    ]
