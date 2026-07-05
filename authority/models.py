from django.conf import settings
from django.db import models


class Authority(models.Model):
    """A first-class legal authority record (architecture doc Section 6.1).

    Every citation used anywhere in the product — on a tax parameter, a
    strategy, or in an issued advice record — points at one of these rows
    rather than existing as a free-text string. Status is a live field:
    marking an authority ``overruled`` should drive editorial review of
    every rule/strategy that links to it (see AuthorityAdmin).
    """

    class AuthorityType(models.TextChoices):
        STATUTE = "statute", "Statute"
        STATUTORY_INSTRUMENT = "si", "Statutory Instrument"
        HMRC_MANUAL = "hmrc_manual", "HMRC Manual Paragraph"
        TRIBUNAL_DECISION = "tribunal", "Tribunal Decision"
        COURT_JUDGMENT = "court", "Court Judgment"

    class Status(models.TextChoices):
        IN_FORCE = "in_force", "In force"
        AMENDED = "amended", "Amended"
        SUPERSEDED = "superseded", "Superseded"
        OVERRULED = "overruled", "Overruled"
        DOUBTED = "doubted", "Doubted"

    authority_type = models.CharField(max_length=20, choices=AuthorityType.choices)

    # e.g. 'IHTA 1984 s.18', 'CG64200', '[2013] UKSC 26'
    canonical_citation = models.CharField(max_length=255, unique=True)

    # legislation.gov.uk / Find Case Law stable URI
    canonical_uri = models.URLField(max_length=500, blank=True)

    date_retrieved = models.DateField()
    verbatim_extract = models.TextField(
        help_text="The verbatim relevant extract from the source, as retrieved."
    )
    archived_snapshot = models.FileField(
        upload_to="authority_snapshots/",
        blank=True,
        null=True,
        help_text="Archived copy of the source (PDF/HTML) as retrieved, because "
        "gov.uk pages change and tribunal links rot.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_FORCE
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "authorities"
        ordering = ["canonical_citation"]

    def __str__(self):
        return self.canonical_citation

    @property
    def needs_review(self):
        return self.status in (self.Status.OVERRULED, self.Status.DOUBTED, self.Status.SUPERSEDED)


class AuthorityStatusChange(models.Model):
    """Append-only log of authority status changes (the case-law
    workflow): when a tribunal or court decision doubts or overrules a
    cited authority, the tax editor records it here with reasons, and
    every dependent strategy becomes reviewable by query. The change
    itself never silently alters advice — the expert panel blocks
    approval of advice citing an overruled authority, and the editorial
    process re-reviews dependent strategies."""

    authority = models.ForeignKey(
        Authority, on_delete=models.CASCADE, related_name="status_changes"
    )
    old_status = models.CharField(max_length=20, choices=Authority.Status.choices)
    new_status = models.CharField(max_length=20, choices=Authority.Status.choices)
    reason = models.TextField(
        help_text="Required: the decision/instrument prompting the change, with citation."
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authority_status_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.authority}: {self.old_status} -> {self.new_status} ({self.changed_at:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuthorityStatusChange is append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuthorityStatusChange cannot be deleted; it is audit history.")


def record_status_change(authority: Authority, user, new_status: str, reason: str):
    """The one sanctioned way to change an authority's status: validates,
    logs append-only, applies. Returns the log entry."""
    if new_status not in Authority.Status.values:
        raise ValueError(f"Unknown authority status: {new_status!r}")
    if not reason.strip():
        raise ValueError(
            "A status change requires a reason citing the decision or instrument "
            "that prompted it."
        )
    if new_status == authority.status:
        raise ValueError("The authority already has that status.")
    change = AuthorityStatusChange(
        authority=authority,
        old_status=authority.status,
        new_status=new_status,
        reason=reason,
        changed_by=user,
    )
    change.save()
    authority.status = new_status
    authority.save(update_fields=["status"])
    return change
