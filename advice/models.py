from django.conf import settings
from django.db import models

from clients.models import Client, ClientFactSet
from firms.models import Firm
from ruleengine.models import RuleBaseRelease


class AdviceRecord(models.Model):
    """An immutable, append-only advice record (architecture doc Section 6.2).

    This is the accountant's defence file: if HMRC challenges advice given
    in 2026, the firm can produce exactly what the tool said, on what data,
    citing what authority as it stood at that date. Records are never
    edited; ``save()``/``delete()`` are locked down below so a correction
    must be a new record via ``supersede()``.
    """

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="advice_records")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="advice_records")
    fact_set = models.ForeignKey(ClientFactSet, on_delete=models.PROTECT, related_name="advice_records")
    tax_year = models.CharField(max_length=7)

    input_data_hash = models.CharField(max_length=64)
    input_data_snapshot = models.JSONField()

    rule_base_release = models.ForeignKey(
        RuleBaseRelease, on_delete=models.PROTECT, related_name="advice_records"
    )
    results = models.JSONField(
        help_text="List of strategy results: quantification, citations, timeframe, risk flags, as generated."
    )
    parameters_used = models.JSONField(
        default=list,
        blank=True,
        help_text="Exact provenance: every TaxParameter row read during generation "
        "(key, row id, effective-from date, introducing release). The numbers in "
        "``results`` are reproducible from these rows alone.",
    )
    rendered_report = models.FileField(upload_to="advice_reports/", blank=True, null=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="advice_generated"
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    superseded_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="supersedes"
    )

    class Meta:
        ordering = ["-generated_at"]
        indexes = [models.Index(fields=["client", "tax_year"])]

    def __str__(self):
        return f"Advice for {self.client.name} ({self.tax_year}) at {self.generated_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError(
                "AdviceRecord is append-only and cannot be modified after creation. "
                "Use AdviceRecord.mark_superseded() to link a correcting record."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AdviceRecord cannot be deleted; it is a permanent audit record.")

    def mark_superseded(self, new_record: "AdviceRecord"):
        AdviceRecord.objects.filter(pk=self.pk).update(superseded_by=new_record)

    def attach_rendered_report(self, filename: str, content_bytes: bytes):
        """Attach the rendered PDF after the record already exists. This is
        the one narrow, explicit exception to append-only: the PDF is a
        byte-for-byte rendering of the already-immutable ``results`` and
        ``input_data_snapshot`` fields, produced in a second step because it
        embeds the record's own primary key. No advice content changes."""
        from django.core.files.base import ContentFile

        self.rendered_report.save(filename, ContentFile(content_bytes), save=False)
        AdviceRecord.objects.filter(pk=self.pk).update(rendered_report=self.rendered_report.name)

    @property
    def is_current(self):
        return self.superseded_by_id is None

    @property
    def has_flagged_strategy(self):
        return any(r.get("risk_status") != "settled" or r.get("dotas_notifiable") or r.get("gaar_exposure") for r in self.results)

    @property
    def latest_panel_review(self):
        return self.panel_reviews.order_by("-created_at").first()

    @property
    def latest_decision(self):
        return self.decisions.order_by("-decided_at").first()


class PanelReview(models.Model):
    """One deployment of the independent expert panel against one advice
    record. The four reviewers (tax lawyer, tax accountant, HMRC
    consultant, business expert — ``advice/panel.py``) are deterministic
    rule sets over the immutable advice record, so a panel review is
    itself reproducible evidence. Append-only, like the advice it reviews.
    """

    class Verdict(models.TextChoices):
        CLEAR = "clear", "Clear — no concerns raised"
        ATTENTION = "attention", "Attention — cautions for the professional"
        BLOCKED = "blocked", "Blocked — must be resolved before approval"

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="panel_reviews")
    advice_record = models.ForeignKey(
        AdviceRecord, on_delete=models.PROTECT, related_name="panel_reviews"
    )
    findings = models.JSONField(
        help_text="All findings from all four reviewers: persona, code, severity, message, strategy."
    )
    verdicts = models.JSONField(
        help_text="Per-persona verdict plus 'overall' (clear/attention/blocked)."
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="panel_reviews_requested"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Panel review of advice {self.advice_record_id}: {self.verdicts.get('overall')}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("PanelReview is append-only; deploy the panel again for a fresh review.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("PanelReview cannot be deleted; it is part of the audit record.")

    @property
    def overall(self):
        return self.verdicts.get("overall")

    @property
    def blockers(self):
        return [f for f in self.findings if f["severity"] == "blocker"]


class AdviceNarrative(models.Model):
    """A validated client-facing narrative draft for an advice record.
    Only drafts that PASSED the §8 validator exist here (create_narrative
    refuses to store rejected drafts); the professional still edits and
    issues it — this is a starting draft, never client-ready by itself.
    Append-only: a redraft is a new row."""

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="narratives")
    advice_record = models.ForeignKey(
        AdviceRecord, on_delete=models.PROTECT, related_name="narratives"
    )
    text = models.TextField()
    drafter = models.CharField(
        max_length=50,
        help_text="What produced the draft, e.g. 'deterministic-v1' or a model id. "
        "All drafters pass the same validator.",
    )
    validation_report = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="narratives_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AdviceNarrative is append-only; draft again instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AdviceNarrative cannot be deleted; it is part of the audit record.")


class AdviceImpactAlert(models.Model):
    """'A rule you relied on has changed': raised per firm, per current
    advice record, when a rule-base release touches parameters behind
    strategies in that advice (architecture doc §5.5 — 'the system can
    list affected clients per firm, enabling firms to proactively
    revisit advice'). The firm reviews and decides whether to regenerate;
    the alert never changes the advice itself."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWED = "reviewed", "Reviewed"

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="impact_alerts")
    advice_record = models.ForeignKey(
        AdviceRecord, on_delete=models.PROTECT, related_name="impact_alerts"
    )
    release = models.ForeignKey(
        RuleBaseRelease, on_delete=models.PROTECT, related_name="impact_alerts"
    )
    affected_strategy_codes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="impact_alerts_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["release", "advice_record"], name="unique_release_advice_impact"
            )
        ]

    def __str__(self):
        return f"Impact of {self.release.version} on advice {self.advice_record_id} [{self.status}]"

    def mark_reviewed(self, user, note=""):
        from django.utils import timezone

        self.status = self.Status.REVIEWED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.note = note
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "note"])


class ProfessionalDecision(models.Model):
    """The human professional's decision on an advice record — only
    possible after the expert panel has reviewed it. This is what makes
    the adviser-of-record boundary operational: the system never releases
    advice; the professional does, on the panel's evidence.
    """

    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved for client"
        REJECTED = "rejected", "Rejected"
        NEEDS_REVISION = "needs_revision", "Needs revision / another way"

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="decisions")
    advice_record = models.ForeignKey(
        AdviceRecord, on_delete=models.PROTECT, related_name="decisions"
    )
    panel_review = models.ForeignKey(
        PanelReview, on_delete=models.PROTECT, related_name="decisions"
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    notes = models.TextField(
        blank=True,
        help_text="Required when approving over blockers, rejecting, or requesting revision.",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="advice_decisions"
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-decided_at"]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("ProfessionalDecision is append-only; record a new decision instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("ProfessionalDecision cannot be deleted; it is part of the audit record.")
