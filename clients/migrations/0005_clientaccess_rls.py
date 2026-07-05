"""Row-level security for access grants, matching the other client tables."""

from django.db import migrations

RLS_SQL = """
ALTER TABLE clients_clientaccess ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients_clientaccess FORCE ROW LEVEL SECURITY;
CREATE POLICY firm_isolation ON clients_clientaccess
    USING (
        CASE current_setting('app.current_firm_id', true)
            WHEN 'ALL' THEN true
            ELSE firm_id = NULLIF(current_setting('app.current_firm_id', true), '')::bigint
        END
    );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS firm_isolation ON clients_clientaccess;
ALTER TABLE clients_clientaccess NO FORCE ROW LEVEL SECURITY;
ALTER TABLE clients_clientaccess DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0004_clientaccess"),
    ]

    operations = [migrations.RunSQL(RLS_SQL, REVERSE_SQL)]
