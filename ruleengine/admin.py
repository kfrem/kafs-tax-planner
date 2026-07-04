from django.contrib import admin

from .models import GoldenTestCase, RuleBaseRelease, Strategy, TaxParameter


@admin.register(RuleBaseRelease)
class RuleBaseReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "status", "effective_date", "editor", "reviewer", "created_at")
    list_filter = ("status",)


class GoldenTestCaseInline(admin.TabularInline):
    model = GoldenTestCase
    extra = 0


@admin.register(TaxParameter)
class TaxParameterAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "tax_domain",
        "effective_range",
        "risk_classification",
        "introduced_in_release",
    )
    list_filter = ("tax_domain", "risk_classification", "introduced_in_release")
    search_fields = ("key", "label")
    filter_horizontal = ("authorities",)


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "tax_domain",
        "timeframe",
        "risk_status",
        "dotas_notifiable",
        "gaar_exposure",
        "introduced_in_release",
    )
    list_filter = ("tax_domain", "timeframe", "risk_status", "dotas_notifiable", "gaar_exposure")
    search_fields = ("name", "code", "plain_english_explanation")
    filter_horizontal = ("authorities",)
    inlines = [GoldenTestCaseInline]


@admin.register(GoldenTestCase)
class GoldenTestCaseAdmin(admin.ModelAdmin):
    list_display = ("description", "calculator_key", "strategy", "source")
    list_filter = ("calculator_key",)
