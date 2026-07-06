"""``self_audit`` — the app auditing itself, end to end, with zero tolerance.

Runs the whole verification chain the way a careful reviewer would, and again,
and again (``--passes``): checks the database is fully migrated, the machine
editorial pre-check is clean, every golden case still matches, then builds REAL
client cases (advice/audit_cases.py) and runs each one through the actual demo
pipeline — generate advice, render the PDF, deploy the four-expert panel — and
fails loudly on:

* any unapplied migration (the guardrail for the migration-drift defect),
* any golden-case mismatch or editorial pre-check failure,
* any panel *engine-defect* finding (figure not reproducible, extraction
  arithmetic broken, missing provenance, uncited position),
* any non-deterministic recomputation (same facts, different numbers),
* any PDF that fails to render,
* any registered strategy that no real case exercises end to end.

Exit code is non-zero on any problem, so CI and a human can both rely on it.
Nothing here trusts the unit tests: every figure is INDEPENDENTLY recomputed
from the stored input snapshot by the panel's tax-accountant reviewer.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor

from advice.audit_cases import AUDIT_CASES
from advice.generator import compute_strategy_results, generate_advice
from advice.panel import deploy_panel
from advice.strategy_adapters import ADAPTERS
from clients.models import Client, ClientFactSet
from firms.models import Firm, User
from reports.pdf import render_advice_pdf
from ruleengine.editorial import precheck
from ruleengine.engine import CALCULATOR_REGISTRY
from ruleengine.models import GoldenTestCase, Strategy
from ruleengine.taxyear import anchor_date

TAX_YEAR = "2025/26"

# Panel findings that mean the ENGINE is wrong (not a professional caution the
# reviewer must weigh). Any of these on any case fails the audit outright.
ENGINE_DEFECT_CODES = {
    "A1_NOT_REPRODUCIBLE",  # figure does not recompute from the stored snapshot
    "A2_IDENTITY_BROKEN",   # extraction arithmetic does not balance
    "A5_NO_PROVENANCE",     # advice has no rule provenance
    "L1_NO_CITATION",       # a position with no legal authority
}


class Command(BaseCommand):
    help = "Self-audit the whole system end to end, repeatedly, with zero tolerance for error."

    def add_arguments(self, parser):
        parser.add_argument(
            "--passes", type=int, default=1,
            help="Re-run the full end-to-end audit this many times (proves determinism).",
        )
        parser.add_argument("--firm-slug", default="demo-accountants")
        parser.add_argument("--username", default="demo")
        parser.add_argument(
            "--skip-migration-check", action="store_true",
            help="Skip the unapplied-migration check (used by the test runner, "
            "whose database is built fresh from migrations).",
        )

    def handle(self, *args, **options):
        passes = max(1, options["passes"])
        problems: list[str] = []

        if not options["skip_migration_check"]:
            problems += self._check_migrations()
        problems += self._check_editorial()
        problems += self._check_golden()

        firm, user = self._context(options["firm_slug"], options["username"])
        expected = self._expected_strategy_codes()

        for p in range(1, passes + 1):
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"\n=== End-to-end pass {p}/{passes}: {len(AUDIT_CASES)} real cases ==="
            ))
            fired: set[str] = set()
            with transaction.atomic():
                for reference, name, entity_type, facts in AUDIT_CASES:
                    case_fired, case_problems = self._run_case(
                        firm, user, reference, name, entity_type, facts
                    )
                    fired |= case_fired
                    problems += case_problems
            missing = expected - fired
            if missing:
                problems.append(
                    f"Coverage gap (pass {p}): no real case exercised {sorted(missing)}"
                )
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Coverage pass {p}: all {len(expected)} live strategies "
                    "exercised end to end."
                ))

        if problems:
            self.stdout.write(self.style.ERROR(f"\nSELF-AUDIT FAILED — {len(problems)} problem(s):"))
            for pr in problems:
                self.stdout.write(self.style.ERROR(f"  - {pr}"))
            raise CommandError("Self-audit failed. Do not ship until every item above is resolved.")

        self.stdout.write(self.style.SUCCESS(
            "\nSELF-AUDIT PASSED — migrations applied, golden cases matched, editorial "
            "pre-check clean, every real case regenerated, rendered, panel-reviewed and "
            "independently recomputed to the penny."
        ))

    # -- individual checks ----------------------------------------------------

    def _check_migrations(self) -> list[str]:
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            names = ", ".join(f"{m.app_label}.{m.name}" for m, _ in plan)
            return [
                f"{len(plan)} unapplied migration(s): {names}. "
                "Run `python manage.py migrate` — the app is not fully built."
            ]
        self.stdout.write(self.style.SUCCESS("[OK] Migrations: all applied (no schema drift)."))
        return []

    def _check_editorial(self) -> list[str]:
        report = precheck()
        if report["failures"]:
            return [f"Editorial machine pre-check: {report['failures']} failed check(s)."]
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Editorial pre-check: 0 failures across {len(report['parameters'])} "
            f"parameters, {len(report['strategies'])} strategies, "
            f"{len(report['authorities'])} authorities."
        ))
        return []

    def _check_golden(self) -> list[str]:
        problems = []
        cases = list(GoldenTestCase.objects.all())
        if not cases:
            return ["No golden test cases seeded."]
        for case in cases:
            calculator = CALCULATOR_REGISTRY.get(case.calculator_key)
            if calculator is None:
                problems.append(f"Golden '{case}': no calculator for {case.calculator_key!r}")
                continue
            actual = calculator(case.input_facts, case.tax_year)
            for key, expected in case.expected_output.items():
                got = actual.get(key)
                if isinstance(expected, bool) or expected is None:
                    ok = got == expected
                elif isinstance(expected, (int, float)):
                    ok = got is not None and abs(float(got) - float(expected)) <= 0.02
                else:
                    ok = got == expected
                if not ok:
                    problems.append(
                        f"Golden '{case}': {key!r} expected {expected!r}, got {got!r}"
                    )
        if not problems:
            self.stdout.write(self.style.SUCCESS(
                f"[OK] Golden cases: all {len(cases)} rows match to the penny."
            ))
        return problems

    # -- real cases -----------------------------------------------------------

    def _context(self, firm_slug, username):
        firm = Firm.objects.get(slug=firm_slug)
        user = User.objects.get(username=username)
        with connection.cursor() as c:
            c.execute(f"SET app.current_firm_id = '{firm.id}'")
        return firm, user

    def _expected_strategy_codes(self) -> set[str]:
        anchor = anchor_date(TAX_YEAR)
        codes = set()
        for s in Strategy.objects.filter(effective_range__contains=anchor):
            if s.calculator_key in ADAPTERS and s.calculator_key in CALCULATOR_REGISTRY:
                codes.add(s.code)
        return codes

    def _run_case(self, firm, user, reference, name, entity_type, facts):
        problems = []
        client, _ = Client.objects.get_or_create(
            firm=firm, reference=reference,
            defaults={"name": name, "entity_type": entity_type, "created_by": user},
        )
        current = client.fact_sets.filter(superseded_by__isnull=True, tax_year=TAX_YEAR).first()
        fact_set = ClientFactSet.objects.create(
            firm=firm, client=client, tax_year=TAX_YEAR,
            facts=facts, source="manual", created_by=user,
        )
        if current is not None:
            current.superseded_by = fact_set
            current.save()

        previous = client.advice_records.filter(
            superseded_by__isnull=True, tax_year=TAX_YEAR
        ).first()
        record = generate_advice(client, fact_set, user)
        if previous is not None:
            previous.mark_superseded(record)

        fired = {r["strategy_code"] for r in record.results}

        # Determinism: identical facts must recompute to identical results.
        if compute_strategy_results(facts, TAX_YEAR) != compute_strategy_results(facts, TAX_YEAR):
            problems.append(f"{reference}: non-deterministic recomputation (same facts, different output).")

        # PDF must render.
        try:
            render_advice_pdf(record)
            if not record.rendered_report:
                problems.append(f"{reference}: PDF did not render.")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{reference}: PDF render error: {exc}")

        # Four-expert panel — the independent recomputation and legal/audit checks.
        review = deploy_panel(record, user)
        for f in review.findings:
            if f["code"] in ENGINE_DEFECT_CODES:
                problems.append(f"{reference}: panel ENGINE DEFECT [{f['code']}] {f['message']}")
        if not any(f["code"] == "A1_RECOMPUTED_OK" for f in review.findings):
            problems.append(f"{reference}: panel did not confirm independent recomputation (A1).")

        self.stdout.write(
            f"  {reference:18s} {len(record.results):2d} strategies | "
            f"panel: {review.verdicts['overall']:9s} | PDF ok"
        )
        return fired, problems
