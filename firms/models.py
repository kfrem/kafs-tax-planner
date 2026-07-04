from django.contrib.auth.models import AbstractUser
from django.db import models


class Firm(models.Model):
    """An accounting firm — the tenant boundary for row-level security.

    The firm is the UK GDPR data controller for its clients' personal data;
    this software is the processor (architecture doc Section 7.1).
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    # Per-firm configurable retention floor, Section 6.3: minimum 6 years
    # after the end of the relevant tax year; firms may elect longer.
    advice_retention_years = models.PositiveIntegerField(default=6)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Firm staff member. Role drives permissions within the firm.

    Superusers (the software vendor's own staff, e.g. the tax editor
    maintaining the rule base via Django Admin) have firm=None and are
    exempt from row-level security (see firms/middleware.py).
    """

    class Role(models.TextChoices):
        PARTNER = "partner", "Partner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    firm = models.ForeignKey(
        Firm, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)

    def __str__(self):
        return self.username

    @property
    def is_partner(self):
        return self.role == self.Role.PARTNER
