from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # Imported for its side effect: this module registers the signal
        # handlers. The name is intentionally unused.
        import notifications.signals  # noqa: F401
