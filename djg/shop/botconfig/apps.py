from django.apps import AppConfig


class BotconfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "botconfig"

    def ready(self) -> None:
        # Register model signal handlers.
        from . import signals  # noqa: F401
