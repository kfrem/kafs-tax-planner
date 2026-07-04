from django.conf import settings
from django.db import models

from firms.models import Firm


class Client(models.Model):
    """A firm's client. Isolated between firms by PostgreSQL row-level
    security (see migration 0002) keyed on ``firm_id``, not only by this
    FK filter in application code (architecture doc Section 7.2)."""

    class EntityType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        COMPANY = "company", "Company"
        INDIVIDUAL_WITH_COMPANY = "individual_with_company", "Individual with own company"

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

    ``facts`` schema (all keys optional, calculators default sensibly):
        personal: {other_income, salary_from_own_company,
                   dividends_from_own_company, spouse_income}
        company: {profit_before_remuneration, employment_allowance_available,
                  associated_companies}
        pension: {threshold_income, adjusted_income,
                  unused_aa_prior_3_years: [y-3, y-2, y-1], desired_contribution}
        sole_trade: {annual_profit}
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
