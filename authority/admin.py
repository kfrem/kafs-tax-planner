from django.contrib import admin

from .models import Authority


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = (
        "canonical_citation",
        "authority_type",
        "status",
        "date_retrieved",
        "needs_review_flag",
    )
    list_filter = ("authority_type", "status")
    search_fields = ("canonical_citation", "verbatim_extract", "notes")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Needs review")
    def needs_review_flag(self, obj):
        return obj.needs_review
