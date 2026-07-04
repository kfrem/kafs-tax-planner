from django.conf import settings
from django.contrib.postgres.fields import DateRangeField
from django.db import models

from authority.models import Authority

from .choices import RiskStatus, TaxDomain, Timeframe


class RuleBaseRelease(models.Model):
    """A versioned release of the rule base (architecture doc Section 5.5).

    Every rule and strategy records which release introduced or amended it,
    and every piece of advice ever generated is stamped with the release in
    force at the time, so historical advice is exactly reproducible.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RELEASED = "released", "Released"

    version = models.CharField(max_length=50, unique=True, help_text="e.g. 2025.1")
    changelog = models.TextField()
    effective_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="edited_releases",
        help_text="The qualified tax professional who drafted this release.",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_releases",
        null=True,
        blank=True,
        help_text="Four-eyes reviewer who approved this release.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return self.version

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.status == self.Status.RELEASED and self.editor_id == self.reviewer_id:
            raise ValidationError(
                "A release cannot be approved by the same person who authored it "
                "(four-eyes review is mandatory — Section 5.6)."
            )
        if self.status == self.Status.RELEASED and not self.reviewer_id:
            raise ValidationError("A released rule-base version requires a reviewer.")


class TaxParameter(models.Model):
    """Layer 1 of the knowledge model: rates, bands, thresholds, allowances.

    Nothing is ever deleted or overwritten (Section 5.1): a change is a new
    row with a new effective range; the old row's range is closed off.
    """

    key = models.CharField(
        max_length=150,
        help_text="Stable dotted identifier, e.g. 'income_tax.personal_allowance'.",
    )
    label = models.CharField(max_length=255)
    tax_domain = models.CharField(max_length=30, choices=TaxDomain.choices)

    effective_range = DateRangeField(
        help_text="Inclusive lower bound, open (unbounded) upper bound while current."
    )

    payload = models.JSONField(
        help_text="Rate/band/threshold/allowance values this parameter carries."
    )

    authorities = models.ManyToManyField(Authority, related_name="tax_parameters", blank=True)
    risk_classification = models.CharField(
        max_length=20, choices=RiskStatus.choices, default=RiskStatus.SETTLED
    )
    introduced_in_release = models.ForeignKey(
        RuleBaseRelease, on_delete=models.PROTECT, related_name="tax_parameters"
    )

    class Meta:
        ordering = ["key", "effective_range"]
        indexes = [models.Index(fields=["key"])]

    def __str__(self):
        return f"{self.key} {self.effective_range}"


class Strategy(models.Model):
    """Layer 3 of the knowledge model: a planning strategy.

    The eligibility/quantification logic lives in Python (ruleengine/engine.py),
    registered against ``calculator_key``; this record carries the parts that
    are the tax editor's professional judgement, not code: applicability
    description, timeframe, risk, and citations.
    """

    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    tax_domain = models.CharField(max_length=30, choices=TaxDomain.choices)

    plain_english_explanation = models.TextField(
        help_text="Why this strategy is legal, authored once by the tax editor."
    )
    eligibility_conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Declarative eligibility conditions evaluated by the engine.",
    )
    calculator_key = models.CharField(
        max_length=100,
        help_text="Key into ruleengine.engine.CALCULATOR_REGISTRY.",
    )

    timeframe = models.CharField(max_length=10, choices=Timeframe.choices)
    risk_status = models.CharField(max_length=20, choices=RiskStatus.choices)
    dotas_notifiable = models.BooleanField(default=False)
    gaar_exposure = models.BooleanField(default=False)

    authorities = models.ManyToManyField(Authority, related_name="strategies", blank=True)

    effective_range = DateRangeField()
    introduced_in_release = models.ForeignKey(
        RuleBaseRelease, on_delete=models.PROTECT, related_name="strategies"
    )

    class Meta:
        ordering = ["tax_domain", "name"]
        verbose_name_plural = "strategies"

    def __str__(self):
        return self.name

    @property
    def is_flagged(self):
        return (
            self.risk_status in (RiskStatus.BORDERLINE, RiskStatus.CONTESTED, RiskStatus.UNTESTED)
            or self.dotas_notifiable
            or self.gaar_exposure
        )


class GoldenTestCase(models.Model):
    """A worked example with a known-correct outcome (Section 5.5).

    The full suite runs in CI on every proposed release; a release that
    changes any golden outcome without an accompanying rule change is
    blocked (see ruleengine/tests/test_golden_cases.py).
    """

    strategy = models.ForeignKey(
        Strategy, on_delete=models.CASCADE, related_name="golden_cases", null=True, blank=True
    )
    calculator_key = models.CharField(
        max_length=100,
        help_text="Calculator this case exercises directly, independent of any strategy.",
    )
    description = models.CharField(max_length=255)
    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'HMRC EIM42200 worked example' or 'band boundary edge case'.",
    )
    tax_year = models.CharField(max_length=7, default="2025/26")
    input_facts = models.JSONField()
    expected_output = models.JSONField()

    class Meta:
        ordering = ["calculator_key", "description"]

    def __str__(self):
        return f"{self.calculator_key}: {self.description}"
