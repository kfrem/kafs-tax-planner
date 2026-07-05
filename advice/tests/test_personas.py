"""Persona consistency suite: every engine change runs against a SIMPLE, a
TYPICAL, and a COMPLEX client (see clients/personas.py) so behaviour is
verified across the whole complexity range, not just the middle.

Three kinds of assertion:
1. Hand-computed expectations pinning specific numbers per persona.
2. Structural invariants every advice record must satisfy (citations
   present, risk status present, provenance captured).
3. Determinism and accounting identities — the same facts must always give
   byte-identical results, and extraction arithmetic must balance.
"""

import pytest

from advice.generator import generate_advice
from clients.models import Client, ClientFactSet
from clients.personas import EMMA_FACTS, SARAH_FACTS, VICTOR_FACTS

TAX_YEAR = "2025/26"
approx = lambda v: pytest.approx(v, abs=0.02)  # noqa: E731

pytestmark = pytest.mark.usefixtures("seeded_rule_base")


@pytest.fixture
def make_advice(firm, staff_user):
    def _make(reference, name, facts):
        client = Client.objects.create(
            firm=firm, reference=reference, name=name,
            entity_type="individual_with_company", created_by=staff_user,
        )
        fact_set = ClientFactSet.objects.create(
            firm=firm, client=client, tax_year=TAX_YEAR,
            facts=facts, source="manual", created_by=staff_user,
        )
        return generate_advice(client, fact_set, staff_user), client, fact_set

    return _make


def _result(record, code):
    return next(r for r in record.results if r["strategy_code"] == code)


class TestEmmaSimple:
    """Low-income employee: the tool must stay quiet where nothing applies,
    and still find the two reliefs that do."""

    def test_only_applicable_strategies_fire(self, make_advice):
        record, _, _ = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        codes = {r["strategy_code"] for r in record.results}
        assert codes == {"marriage-allowance-transfer", "pension-annual-allowance-carry-forward"}

    def test_marriage_allowance_eligible_and_quantified(self, make_advice):
        # Emma 9,000 < PA, spouse 30,000 basic rate: transfer 1,260 saves
        # 1,260 x 20% = 252.
        record, _, _ = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        q = _result(record, "marriage-allowance-transfer")["quantification"]
        assert q["eligible"] is True
        assert q["estimated_annual_tax_saving"] == approx(252.0)

    def test_small_pension_gets_basic_credit_only(self, make_advice):
        # Emma's 9,000 employment income counts as relevant UK earnings, so
        # the 2,000 contribution is fully relievable; she is below the
        # personal allowance, so relief is the 20% credit (400) only; no
        # employer route (no company).
        record, _, _ = make_advice("H001", "Emma Hughes", EMMA_FACTS)
        q = _result(record, "pension-annual-allowance-carry-forward")["quantification"]
        assert q["personal_route"]["relievable_gross"] == approx(2000.0)
        assert q["personal_route"]["basic_rate_credit_to_pension"] == approx(400.0)
        assert q["personal_route"]["unrelieved_amount"] == approx(0.0)
        assert q["employer_route"] is None


class TestVictorComplex:
    """Additional-rate owner-manager: taper interactions everywhere."""

    def test_pension_annual_allowance_is_tapered(self, make_advice):
        # threshold 300k / adjusted 350k -> excess 90k -> reduction 45k ->
        # AA 15,000 + carry-forward 90,000 = 105,000 available; desired
        # 120,000 -> 15,000 exposed to the annual allowance charge.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "pension-annual-allowance-carry-forward")["quantification"]
        assert q["available_annual_allowance"] == approx(105000.0)
        assert q["fits_within_allowance"] is False
        assert q["amount_subject_to_annual_allowance_charge"] == approx(15000.0)

    def test_pension_earnings_cap_and_employer_route(self, make_advice):
        # Relevant earnings = 85,000 sole trade (rental income excluded):
        # personal relief capped there, 35,000 unrelieved. Employer route:
        # 120,000 from 480,000 profit, flat 25% -> CT saving 30,000.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "pension-annual-allowance-carry-forward")["quantification"]
        assert q["relevant_uk_earnings"] == approx(85000.0)
        assert q["personal_route"]["relievable_gross"] == approx(85000.0)
        assert q["personal_route"]["unrelieved_amount"] == approx(35000.0)
        assert q["employer_route"]["corporation_tax_saving"] == approx(30000.0)

    def test_marriage_allowance_correctly_refused(self, make_advice):
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "marriage-allowance-transfer")["quantification"]
        assert q["eligible"] is False

    def test_rnrb_fully_tapered_on_large_estate(self, make_advice):
        # Combined 4.5m estate: 2.5m over the 2m threshold wipes out even
        # a doubled RNRB (350k - 1.25m taper -> 0). Transferable-band value
        # is the NRB transfer only: 325,000 x 40% = 130,000.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "iht-spousal-transfer-and-nil-rate-bands")["quantification"]
        assert q["rnrb_taper_applies"] is True
        assert q["second_death_with_transferred_bands"]["residence_nil_rate_band"] == 0.0
        assert q["second_death_with_transferred_bands"]["tax_due"] == approx(1540000.0)
        assert q["second_death_without_claims"]["tax_due"] == approx(1670000.0)
        assert q["value_of_transferable_bands"] == approx(130000.0)

    def test_large_gift_saving(self, make_advice):
        # 500,000 gift from 4.5m estate: RNRB stays tapered to zero either
        # side, so saving is a clean 40% x 500,000 = 200,000.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "iht-lifetime-gifting-pets")["quantification"]
        assert q["saving_if_survive_7_years"] == approx(200000.0)

    def test_spousal_cgt_transfer_honest_about_small_saving(self, make_advice):
        # Both spouses are higher-rate taxpayers, so splitting the 150,000
        # rental gain saves exactly the second annual exempt amount at 24%:
        # 3,000 x 24% = 720. The tool must report that honestly.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "cgt-spousal-transfer-before-disposal")["quantification"]
        assert q["cgt_disposing_alone"] == approx(35280.0)
        assert q["saving"] == approx(720.0)

    def test_ppr_not_offered_on_never_occupied_rental(self, make_advice):
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        codes = {r["strategy_code"] for r in record.results}
        assert "cgt-ppr-relief" not in codes

    def test_charity_top_up_arithmetic(self, make_advice):
        # Baseline 4.5m - 650k = 3.85m -> target 385,000; current 50,000.
        # Current tax: (4.5m - 50k - 650k) at 40% = 1,520,000. At target:
        # (4.5m - 385k - 650k) = 3.465m at 36% = 1,247,400 -> saving
        # 272,600; net cost 335,000 - 272,600 = 62,400.
        record, _, _ = make_advice("A007", "Victor Adeyemi", VICTOR_FACTS)
        q = _result(record, "iht-charitable-legacy-reduced-rate")["quantification"]
        assert q["target_legacy_for_reduced_rate"] == approx(385000.0)
        assert q["current_position"]["tax_due"] == approx(1520000.0)
        assert q["extra_charitable_legacy_needed"] == approx(335000.0)
        assert q["tax_saving"] == approx(272600.0)
        assert q["net_cost_to_beneficiaries"] == approx(62400.0)


class TestCrossPersonaInvariants:
    """Structural guarantees that must hold for every client, simple or not."""

    @pytest.mark.parametrize(
        "reference,name,facts",
        [
            ("H001", "Emma Hughes", EMMA_FACTS),
            ("M042", "Sarah Mitchell", SARAH_FACTS),
            ("A007", "Victor Adeyemi", VICTOR_FACTS),
        ],
    )
    def test_every_result_is_fully_attributed(self, make_advice, reference, name, facts):
        record, _, _ = make_advice(reference, name, facts)
        assert record.results, "at least one strategy must fire"
        for r in record.results:
            assert r["authorities"], f"{r['strategy_code']} has no citation"
            assert r["risk_status"] in ("settled", "borderline", "contested", "untested")
            assert r["timeframe"] in ("short", "medium", "long")
        assert record.parameters_used, "provenance must be captured"
        assert all(p["release"] for p in record.parameters_used)

    @pytest.mark.parametrize(
        "reference,name,facts",
        [
            ("H001", "Emma Hughes", EMMA_FACTS),
            ("M042", "Sarah Mitchell", SARAH_FACTS),
            ("A007", "Victor Adeyemi", VICTOR_FACTS),
        ],
    )
    def test_generation_is_deterministic(self, make_advice, reference, name, facts):
        record1, client, fact_set = make_advice(reference, name, facts)
        record2 = generate_advice(client, fact_set, record1.generated_by)
        assert record1.results == record2.results
        assert record1.parameters_used == record2.parameters_used
        assert record1.input_data_hash == record2.input_data_hash

    @pytest.mark.parametrize(
        "reference,name,facts",
        [
            ("M042", "Sarah Mitchell", SARAH_FACTS),
            ("A007", "Victor Adeyemi", VICTOR_FACTS),
        ],
    )
    def test_extraction_arithmetic_balances(self, make_advice, reference, name, facts):
        # net = salary + dividends - employee NIC - personal tax, to the
        # penny, for every comparison row the optimiser reports.
        record, _, _ = make_advice(reference, name, facts)
        q = _result(record, "salary-dividend-mix")["quantification"]
        for row in q["comparisons"]:
            expected_net = (
                row["salary"]
                + row["dividends_available"]
                - row["employee_nic"]
                - row["personal_tax_on_extraction"]
            )
            assert row["net_to_individual"] == approx(expected_net)
