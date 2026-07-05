# Engineering playbook for AI-assisted accounting software

**How to use this document:** paste it, whole, into your AI coding
assistant (Codex, Claude, or any other) as standing project
instructions, with this preamble: *"These are the engineering standards
for this project. Follow every numbered rule. When a rule conflicts
with speed, the rule wins. Confirm in each work summary which rules the
change exercised."*

It was extracted from the build of a UK tax-planning system where every
figure carries professional liability. Everything here is free — no
paid tooling anywhere.

---

## A. Correctness rules (the non-negotiables)

**A1. Hand-compute every test expectation.** A test must assert what
the legislation / accounting standard / arithmetic says, worked out by
hand (or taken from a published official example) — never what the code
returned last time you ran it. Show the working in a comment:

```python
def test_gain_straddles_basic_band():
    # Earned 42,270 -> taxable 29,700 -> 8,000 of basic band left.
    # Gain 15,000 - 3,000 exemption = 12,000: 8,000 @ 18% + 4,000 @ 24%
    # = 1,440 + 960 = 2,400.
    assert result["tax_due"] == approx(2400.00)
```
Snapshot tests ("assert output == saved output") only prove the code
hasn't changed, not that it was ever right. Twice during our build the
hand-computation caught an error **in the test author's own arithmetic**
before it shipped — the discipline checks the human too.

**A2. Use Decimal, not float, for ledger money.** Any double-entry
ledger, VAT computation, or balance that must reconcile to the penny
uses `Decimal` with explicit quantisation rules, never binary floats.
(Planning/estimation figures may use floats with a defined rounding
boundary, but state that decision in writing.)

**A3. Enforce accounting identities as automated tests.** Debits equal
credits on every posting. Control accounts equal subledger totals. A
trial balance nets to zero. Net pay = gross − deductions to the penny.
Write these as *parametrised invariant tests that run against every
scenario in the suite*, not as one example. Identities catch entire
classes of bug that example-based tests miss.

**A4. Calculations must be pure and deterministic.** A calculation
function receives facts + a rule version and returns the same answer
forever: no wall-clock reads, no randomness, no network, no hidden
global state. Include a test that runs the same input twice and asserts
byte-identical output. If AI/LLM features exist, they may draft prose
around computed numbers — an LLM output is NEVER the source of a
number, a rate, or a compliance decision.

**A5. Rates and rules are data, not code.** Tax rates, VAT thresholds,
allowances, band limits live in database rows with effective-from/to
dates, editable without a deploy. A rate change is a new row; the old
row is closed, never edited or deleted, so prior-period computations
stay reproducible forever. Version these rows in named releases with a
changelog and (for regulated content) a second-person approval; rows
belonging to unapproved releases must be invisible to the engine — a
gate enforced in the data-access function, not in procedure.

**A6. Golden test cases live in the database and run in CI.** Keep a
table of worked examples (inputs + hand-verified outputs, with the
source of each). A data-driven test executes all of them. Adding a
worked example to the data automatically adds test coverage. A release
that changes any golden outcome without an accompanying rule change
must fail the build.

## B. Audit-trail rules

**B1. Outputs that matter are append-only.** Invoices, postings, filed
returns, generated advice: `save()` refuses updates after creation,
`delete()` refuses always, corrections are new records linked to what
they supersede. Enforce in the model layer so even privileged code
cannot bypass it. (During our build, the developer tried to delete a
test record during cleanup and the model refused — that refusal is the
feature.)

**B2. Record provenance on every output.** Each stored output carries:
a hash + snapshot of its inputs, the exact rule/rate rows read (row ids
and versions), the software context, who, and when. Test that the
provenance is captured and that recomputing from snapshot + rows
reproduces the output exactly.

**B3. Multi-tenant isolation belongs in the database.** If multiple
clients/companies share one database, use PostgreSQL row-level security
keyed to a session variable — not just `WHERE` clauses in application
code. The application must connect as a **non-superuser** role in dev,
CI, and production (superusers bypass RLS silently). Write a test that
proves cross-tenant reads and writes fail *at the database*.

## C. Testing structure

**C1. Three personas bracketing complexity.** Maintain canonical test
clients: one so simple most features shouldn't trigger (proves the
system stays quiet — over-firing on simple cases is its own defect),
one typical, one complex enough to engage every threshold, taper and
edge interaction at once. Run all three through the full pipeline on
every change, with pinned hand-computed expectations.

**C2. Structural invariants across all personas.** Parametrised tests
asserting what must hold for *every* output: every figure attributed to
a rule version, every regulated statement carrying its required
disclosures, determinism, and the A3 identities.

**C3. Test the failure modes deliberately.** Stale rules detected
(recompute-and-diff), unapproved rule rows ignored, deletion refused,
cross-tenant access refused, resolution-without-notes refused. The
guard rails need tests as much as the happy paths.

**C4. External calls behind injectable interfaces.** Anything touching
the network (bank feeds, HMRC APIs, web watchers) takes an injectable
fetcher/client so tests stub it. No network in tests, ever. Failures in
one external call are recorded and skipped, never fatal to the batch.

## D. CI pipeline (all free on GitHub Actions)

Run on every push and pull request; a red build means do not merge.

```yaml
jobs:
  test:
    # PostgreSQL service container (same major version as production),
    # a NON-superuser app role created before tests, then:
    #   python -m pytest -q
    # Also: python manage.py check --deploy --fail-level ERROR
  lint:
    #   ruff check .          (style + real bug patterns, seconds)
    #   pip-audit -r requirements.txt   (known CVEs in dependencies)
  docker-image:
    #   docker build .        (a broken build/packaging can't reach main)
```

Plus: pin dependency versions in requirements.txt; enable GitHub
Dependabot alerts (free); enable branch protection requiring CI green
before merge if your plan allows it (free on public repos) — otherwise
the team rule is simply that red means stop.

## E. Working practices for the AI assistant

**E1. Keep a defect log.** Every bug found — including bugs in your own
test expectations — goes in a handover document: what happened, the
fix, the regression test that now pins it. Honesty compounds; hidden
defects don't.

**E2. Document simplifications at the point of code.** Every deliberate
shortcut ("dividend allowance modelled as X", "no multi-currency yet")
is written in the docstring where it lives AND collected in one list a
domain reviewer can work through.

**E3. Layered documentation, updated in the same change.**
ARCHITECTURE (as built, with the invariants that must never break),
DEVELOPER_HANDOVER (build log with test counts per step, setup from
nothing ending in "run the suite; N passing means you've reproduced my
results", conventions, defect log, remaining work), TEST_EVIDENCE
(inventory of what each test file proves, how to run, last results).

**E4. Definition of done for any feature** — all six, no exceptions:
implementation · hand-computed tests · invariants still green · docs
updated · defect log updated if anything was found · CI green.

**E5. New rule/rate = data change, not code change.** If you find
yourself editing a calculator for a rate change, stop: the design is
wrong or you are.

**E6. Idempotent seed commands.** Dev, CI, and demo environments are
built by re-runnable management commands, so every environment
converges on the same state and the reproduction check in E3 works.

---

*Provenance: distilled from the KAFS UK Tax Planner build (Django /
PostgreSQL, 119 hand-computed tests, 16 golden cases, CI + container
build on every push). The practices transfer to any software where the
numbers must be right and provably so.*
