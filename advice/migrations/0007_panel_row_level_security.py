"""Row-level security for the panel tables, mirroring advice_advicerecord:
panel reviews and professional decisions contain client-derived data and
must be firm-isolated at the database layer."""

from django.db import migrations

TABLES = ["advice_panelreview", "advice_professionaldecision"]

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
        ("advice", "0006_panelreview_professionaldecision"),
    ]

    operations = [
        migrations.RunSQL(RLS_SQL.format(table=table), REVERSE_SQL.format(table=table))
        for table in TABLES
    ]
