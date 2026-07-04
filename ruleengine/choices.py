from django.db import models


class RiskStatus(models.TextChoices):
    """Layer 5 of the knowledge model (architecture doc Section 5.2)."""

    SETTLED = "settled", "Settled"
    BORDERLINE = "borderline", "Borderline"
    CONTESTED = "contested", "Contested"
    UNTESTED = "untested", "Untested"


class Timeframe(models.TextChoices):
    SHORT = "short", "Short-term (within 1 year)"
    MEDIUM = "medium", "Medium-term (within 3 years)"
    LONG = "long", "Long-term (4 years or more)"


class TaxDomain(models.TextChoices):
    PERSONAL_INCOME_TAX = "personal_income_tax", "Personal Income Tax"
    CORPORATION_TAX = "corporation_tax", "Corporation Tax"
    INHERITANCE_TAX = "inheritance_tax", "Inheritance Tax"
    CROSS_CUTTING = "cross_cutting", "Cross-cutting"
