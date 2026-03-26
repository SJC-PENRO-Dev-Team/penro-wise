from django.apps import AppConfig
import os


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # --------------------------------------------------
        # Load signals (REQUIRED)
        # --------------------------------------------------
        import notifications.signals  # noqa

        # --------------------------------------------------
        # Start APScheduler SAFELY
        # --------------------------------------------------
        # Prevent duplicate scheduler from Django autoreload (development only)
        # In production (Gunicorn), RUN_MAIN is not set, so we check for it
        run_main = os.environ.get("RUN_MAIN")
        
        # Start scheduler if:
        # 1. In production (RUN_MAIN not set), OR
        # 2. In development with autoreload (RUN_MAIN == "true")
        if run_main is None or run_main == "true":
            from .scheduler import start_scheduler
            start_scheduler()
