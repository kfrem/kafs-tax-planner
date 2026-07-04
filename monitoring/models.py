"""Change-monitoring pipeline (architecture doc §5.4): watchers over the
primary sources every authority record cites. Watchers DETECT AND DIFF;
they never change a rule. Every detected change lands in this editorial
queue, where the human tax editor assesses impact and, if action is
needed, ships it as a new rule-base release under four-eyes review.

These tables hold rule-base-level data (no client information), so they
are staff-only at the view layer rather than firm-isolated by RLS.
"""

from django.conf import settings
from django.db import models

from authority.models import Authority
from ruleengine.models import RuleBaseRelease


class WatchedSource(models.Model):
    """One primary-source URL under watch, normally the canonical URI of an
    authority record (legislation.gov.uk section, HMRC manual page, Find
    Case Law judgment)."""

    class SourceType(models.TextChoices):
        LEGISLATION = "legislation", "legislation.gov.uk"
        HMRC_MANUAL = "hmrc_manual", "HMRC manual page"
        CASE_LAW = "case_law", "Find Case Law / judgment"
        OTHER = "other", "Other"

    authority = models.ForeignKey(
        Authority, on_delete=models.CASCADE, null=True, blank=True,
        related_name="watched_sources",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    label = models.CharField(max_length=255)
    url = models.URLField(max_length=500, unique=True)
    active = models.BooleanField(default=True)

    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_fingerprint = models.CharField(
        max_length=64, blank=True,
        help_text="SHA-256 of the normalised page text at the last check.",
    )
    last_content_snapshot = models.TextField(
        blank=True,
        help_text="Normalised text at the last check, kept so the next change "
        "can be diffed against it (and as evidence of what was seen when).",
    )

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return self.label


class ChangeAlert(models.Model):
    """An editorial queue item: this watched source's content changed.
    Advisory only — resolving an alert never writes to the rule base; the
    editor does that through the normal release process and links the
    release here for the audit trail."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        UNDER_REVIEW = "under_review", "Under review"
        ACTIONED = "actioned", "Actioned (rule-base release)"
        DISMISSED = "dismissed", "Dismissed (no rule impact)"

    source = models.ForeignKey(WatchedSource, on_delete=models.CASCADE, related_name="alerts")
    detected_at = models.DateTimeField(auto_now_add=True)
    previous_fingerprint = models.CharField(max_length=64)
    new_fingerprint = models.CharField(max_length=64)
    diff_excerpt = models.TextField(
        help_text="Unified diff of the normalised text (truncated). The editor "
        "reads the primary source before acting — this is a pointer, not the "
        "authority."
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="change_alerts_reviewed",
    )
    resolution_notes = models.TextField(blank=True)
    actioned_in_release = models.ForeignKey(
        RuleBaseRelease, on_delete=models.PROTECT, null=True, blank=True,
        related_name="change_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"Change in {self.source.label} at {self.detected_at:%Y-%m-%d %H:%M} [{self.status}]"

    def dependent_strategies(self):
        """Which strategies cite the authority behind this source — the
        §5.3 impact query, surfaced in the queue so the editor sees blast
        radius immediately."""
        if self.source.authority_id is None:
            return []
        return list(self.source.authority.strategies.all())

    def mark_under_review(self, user):
        self.status = self.Status.UNDER_REVIEW
        self.reviewed_by = user
        self.save(update_fields=["status", "reviewed_by"])

    def resolve(self, user, status, notes, release=None):
        from django.utils import timezone

        if status not in (self.Status.ACTIONED, self.Status.DISMISSED):
            raise ValueError("Resolution must be 'actioned' or 'dismissed'.")
        if not notes.strip():
            raise ValueError(
                "Resolving an alert requires notes: what was checked against the "
                "primary source and why this outcome."
            )
        if status == self.Status.ACTIONED and release is None:
            raise ValueError(
                "An actioned alert must reference the rule-base release that "
                "carries the change."
            )
        self.status = status
        self.reviewed_by = user
        self.resolution_notes = notes
        self.actioned_in_release = release
        self.resolved_at = timezone.now()
        self.save(
            update_fields=[
                "status", "reviewed_by", "resolution_notes",
                "actioned_in_release", "resolved_at",
            ]
        )
