from django.apps import AppConfig


class RuleengineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ruleengine"

    def ready(self):
        from . import calculators  # noqa: F401  registers CALCULATOR_REGISTRY entries
