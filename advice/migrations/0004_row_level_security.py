"""See clients/migrations/0003_row_level_security.py for rationale."""

from django.db import migrations

RLS_SQL = """
ALTER TABLE advice_advicerecord ENABLE ROW LEVEL SECURITY;
ALTER TABLE advice_advicerecord FORCE ROW LEVEL SECURITY;
CREATE POLICY firm_isolation ON advice_advicerecord
    USING (
        CASE current_setting('app.current_firm_id', true)
            WHEN 'ALL' THEN true
            ELSE firm_id = NULLIF(current_setting('app.current_firm_id', true), '')::bigint
        END
    );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS firm_isolation ON advice_advicerecord;
ALTER TABLE advice_advicerecord NO FORCE ROW LEVEL SECURITY;
ALTER TABLE advice_advicerecord DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("advice", "0003_initial"),
    ]

    operations = [migrations.RunSQL(RLS_SQL, REVERSE_SQL)]
