"""Ferzion Discovery — Methodology / AppConfig."""

from django.apps import AppConfig


class MethodologyConfig(AppConfig):
    """Configuração do app Methodology."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.methodology"
    label = "methodology"
    verbose_name = "Metodologia"

    def ready(self) -> None:
        """Importa sinais e configurações no startup."""
        from . import signals  # noqa: F401  -- registra signal handlers
