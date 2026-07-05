"""Row-level security for impact alerts: they reference client advice, so
they are firm-isolated like every other client-data table."""

from django.db import migrations

RLS_SQL = """
ALTER TABLE advice_adviceimpactalert ENABLE ROW LEVEL SECURITY;
ALTER TABLE advice_adviceimpactalert FORCE ROW LEVEL SECURITY;
CREATE POLICY firm_isolation ON advice_adviceimpactalert
    USING (
        CASE current_setting('app.current_firm_id', true)
            WHEN 'ALL' THEN true
            ELSE firm_id = NULLIF(current_setting('app.current_firm_id', true), '')::bigint
        END
    );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS firm_isolation ON advice_adviceimpactalert;
ALTER TABLE advice_adviceimpactalert NO FORCE ROW LEVEL SECURITY;
ALTER TABLE advice_adviceimpactalert DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("advice", "0008_adviceimpactalert"),
    ]

    operations = [migrations.RunSQL(RLS_SQL, REVERSE_SQL)]
