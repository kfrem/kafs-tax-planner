from django.contrib import admin

from .models import AdviceRecord


@admin.register(AdviceRecord)
class AdviceRecordAdmin(admin.ModelAdmin):
    """Read-only in Admin: advice records are append-only (Section 6.2)."""

    list_display = ("client", "tax_year", "firm", "rule_base_release", "generated_by", "generated_at", "is_current")
    list_filter = ("firm", "tax_year", "rule_base_release")
    readonly_fields = [f.name for f in AdviceRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True)
    def is_current(self, obj):
        return obj.is_current
