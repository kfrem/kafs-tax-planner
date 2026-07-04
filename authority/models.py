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
