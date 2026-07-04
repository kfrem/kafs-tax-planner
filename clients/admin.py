from django.contrib import admin

from .models import Client, ClientFactSet


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "reference", "firm", "entity_type", "is_active", "created_at")
    list_filter = ("firm", "entity_type", "is_active")
    search_fields = ("name", "reference")


@admin.register(ClientFactSet)
class ClientFactSetAdmin(admin.ModelAdmin):
    list_display = ("client", "tax_year", "firm", "source", "created_at", "is_current")
    list_filter = ("firm", "tax_year", "source")

    @admin.display(boolean=True)
    def is_current(self, obj):
        return obj.is_current
