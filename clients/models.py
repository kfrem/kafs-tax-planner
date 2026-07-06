from django.conf import settings
from django.db import models

from firms.models import Firm


class Client(models.Model):
    """A firm's client. Isolated between firms by PostgreSQL row-level
    security (see migration 0002) keyed on ``firm_id``, not only by this
    FK filter in application code (architecture doc Section 7.2)."""

    class EntityType(models.TextChoices):
        # NB: the entity type is a filing/reporting label only — it does NOT
        # gate which strategies apply. Eligibility is driven entirely by the
        # facts recorded for the client (see advice/strategy_adapters.py), so a
        # client is whatever their facts say. These labels exist so the firm can
        # categorise and report; adding one never changes the tax planning.
        INDIVIDUAL = "individual", "Individual"
        SOLE_TRADER = "sole_trader", "Sole trader"
        PARTNERSHIP = "partnership", "Partnership / LLP"
        COMPANY = "company", "Company"
        INDIVIDUAL_WITH_COMPANY = "individual_with_company", "Individual with own company"
        TRUST = "trust", "Trust"
        ESTATE = "estate", "Estate (in administration)"

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="clients")
    reference = models.CharField(max_length=50, help_text="Firm's own client reference/code.")
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=30, choices=EntityType.choices)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="clients_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["firm", "reference"], name="unique_client_reference_per_firm")
        ]

    def __str__(self):
        return f"{self.name} ({self.firm.name})"


class ClientFactSet(models.Model):
    """Client financial facts for one tax year (architecture doc Section 4:
    Client Data Module). Versioned per tax year and per firm; never edited
    in place once used to generate advice — a correction is a new row
    (``superseded_by`` chains to the replacement) so that regenerating
    historical advice is possible.

    ``facts`` is an open JSON document of optional "buckets"; every calculator
    defaults sensibly when a key is absent, and eligibility is driven by which
    facts are present (not by the client's entity_type label). The buckets in
    use today — a client populates only the ones that apply to them:
        personal:   {other_income, employment_income, salary_from_own_company,
                     dividends_from_own_company, spouse_income, gift_aid_donation,
                     salary_sacrifice_amount, desired_pension_contribution,
                     divisible_capital_gain, isa_amount_to_shelter,
                     isa_realised_gain, isa_annual_dividend_income,
                     venture_capital_investment/scheme/gain_reinvested,
                     income_tax_liability}
        company:    {profit_before_remuneration, employment_allowance_available,
                     associated_companies, desired_employer_pension_contribution,
                     surrendering_company_loss, claimant_company_profit,
                     overdrawn_loan_balance, repaid_within_9_months,
                     qualifying_capital_spend}
        sole_trade: {annual_profit}
        pension:    {threshold_income, adjusted_income,
                     unused_aa_prior_3_years: [y-3, y-2, y-1], desired_contribution}
        property:   {disposal_gain, disposal_asset_type, ownership_months,
                     occupied_as_main_residence_months,
                     shared_occupancy_let_fraction, spouse_available_for_transfer,
                     badr_qualifying_gain, purchase_price, jurisdiction,
                     property_type, is_additional_dwelling,
                     lease_annual_rent, lease_term_years, lease_premium}
        estate:     {gross_value, liabilities, home_equity_value,
                     home_passes_to_direct_descendants, qualifying_business_property,
                     combined_estate_second_death, combined_home_equity_second_death,
                     charitable_legacy, planned_lifetime_gift,
                     prior_year_annual_exemption_unused, transferred_nrb/rnrb_fraction}
    """

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="fact_sets")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="fact_sets")
    tax_year = models.CharField(max_length=7, help_text="e.g. 2025/26")

    facts = models.JSONField(default=dict)

    source = models.CharField(
        max_length=20,
        choices=[("manual", "Manual entry"), ("csv_import", "CSV import")],
        default="manual",
    )
    superseded_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="supersedes"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="fact_sets_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["client", "tax_year"])]

    def __str__(self):
        return f"{self.client.name} facts {self.tax_year}"

    @property
    def is_current(self):
        return self.superseded_by_id is None


class ClientAccess(models.Model):
    """Per-client access grant (architecture doc §7.2 'per-client access
    controls'): partners and managers see every client in their firm;
    STAFF users see only clients they have been granted. Enforced through
    ``accessible_clients()`` in every view that touches client data —
    on top of (never instead of) the firm-level row-level security."""

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="client_access_grants")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="access_grants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_access_grants"
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="client_access_granted"
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "user"], name="unique_client_user_access")
        ]

    def __str__(self):
        return f"{self.user} -> {self.client}"


def accessible_clients(user):
    """The clients this user may work on. Partners/managers: whole firm.
    Staff: only granted clients."""
    base = Client.objects.filter(firm=user.firm, is_active=True)
    if user.is_superuser or user.role in ("partner", "manager"):
        return base
    return base.filter(access_grants__user=user)


def get_accessible_client_or_404(user, pk):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(accessible_clients(user), pk=pk)
