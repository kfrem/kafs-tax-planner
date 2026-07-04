from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Firm, User


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "advice_retention_years", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Firm membership", {"fields": ("firm", "role")}),
    )
    list_display = ("username", "email", "firm", "role", "is_staff", "is_superuser")
    list_filter = ("firm", "role", "is_staff", "is_superuser")
