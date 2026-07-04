from django.contrib import admin

from .models import ChangeAlert, WatchedSource


@admin.register(WatchedSource)
class WatchedSourceAdmin(admin.ModelAdmin):
    list_display = ("label", "source_type", "active", "last_checked_at")
    list_filter = ("source_type", "active")
    search_fields = ("label", "url")


@admin.register(ChangeAlert)
class ChangeAlertAdmin(admin.ModelAdmin):
    list_display = ("source", "detected_at", "status", "reviewed_by", "actioned_in_release")
    list_filter = ("status",)
    readonly_fields = ("source", "detected_at", "previous_fingerprint", "new_fingerprint", "diff_excerpt")
