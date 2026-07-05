"""Row-level security for narratives: client-facing content, firm-isolated."""

from django.db import migrations

RLS_SQL = """
ALTER TABLE advice_advicenarrative ENABLE ROW LEVEL SECURITY;
ALTER TABLE advice_advicenarrative FORCE ROW LEVEL SECURITY;
CREATE POLICY firm_isolation ON advice_advicenarrative
    USING (
        CASE current_setting('app.current_firm_id', true)
            WHEN 'ALL' THEN true
            ELSE firm_id = NULLIF(current_setting('app.current_firm_id', true), '')::bigint
        END
    );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS firm_isolation ON advice_advicenarrative;
ALTER TABLE advice_advicenarrative NO FORCE ROW LEVEL SECURITY;
ALTER TABLE advice_advicenarrative DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("advice", "0010_advicenarrative"),
    ]

    operations = [migrations.RunSQL(RLS_SQL, REVERSE_SQL)]
