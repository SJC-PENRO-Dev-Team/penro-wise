from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# ============================================================
# GLOBAL SAFETY LOCK
# Prevents scheduler from starting more than once
# ============================================================
_scheduler = None


def start_scheduler():
    """
    Start APScheduler safely.

    - Respects ENABLE_SCHEDULER setting
    - Prevents double start (Django autoreload, imports)
    - Safe for development and single-process production
    """
    global _scheduler

    # --------------------------------------------
    # DEV / PROD TOGGLE
    # --------------------------------------------
    if not getattr(settings, "ENABLE_SCHEDULER", False):
        logger.info("APScheduler disabled via settings (ENABLE_SCHEDULER=False)")
        return

    # --------------------------------------------
    # SAFETY LOCK (NO DOUBLE START)
    # --------------------------------------------
    if _scheduler is not None:
        logger.info("APScheduler already running, skipping initialization")
        return

    logger.info("Starting APScheduler...")

    _scheduler = BackgroundScheduler(
        timezone=settings.TIME_ZONE
    )

    # --------------------------------------------
    # SCHEDULE: DEADLINE REMINDERS (5× DAILY)
    # Every 4 hours 48 minutes
    # --------------------------------------------
    _scheduler.add_job(
        run_deadline_reminders,
        trigger="interval",
        hours=4,
        minutes=48,
        id="send_deadline_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: CLEANUP REJECTED FILES (HOURLY)
    # Deletes rejected files after 24-hour grace period
    # --------------------------------------------
    _scheduler.add_job(
        run_cleanup_rejected_files,
        trigger="interval",
        hours=1,
        id="cleanup_rejected_files",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: PROCESS WORKCYCLE JOBS (EVERY 2 MINUTES)
    # Processes pending WorkCycleJob records for async processing
    # --------------------------------------------
    _scheduler.add_job(
        run_process_workcycle_jobs,
        trigger="interval",
        minutes=2,
        id="process_workcycle_jobs",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: PROCESS WORKCYCLE EMAIL JOBS (EVERY 1 MINUTE)
    # Processes pending WorkCycleEmailJob records for async email sending
    # --------------------------------------------
    _scheduler.add_job(
        run_process_workcycle_email_jobs,
        trigger="interval",
        minutes=1,
        id="process_workcycle_email_jobs",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: PROCESS WORKITEM JOBS (EVERY 1 MINUTE)
    # Processes pending WorkItemStatusJob and WorkItemReviewJob records
    # --------------------------------------------
    _scheduler.add_job(
        run_process_workitem_jobs,
        trigger="interval",
        minutes=1,
        id="process_workitem_jobs",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: SEND MESSAGE DIGESTS (EVERY 6 HOURS)
    # Sends email digests for unread messages
    # --------------------------------------------
    _scheduler.add_job(
        run_send_message_digests,
        trigger="interval",
        hours=6,
        id="send_message_digests",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --------------------------------------------
    # SCHEDULE: CLEAR OLD MESSAGE NOTIFICATIONS (WEEKLY)
    # Clears old message notifications every Sunday
    # --------------------------------------------
    _scheduler.add_job(
        run_clear_message_notifications,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="clear_message_notifications",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    _scheduler.start()

    logger.info(
        "APScheduler started:\n"
        "  - Deadline reminders: every 4h 48m (5× daily)\n"
        "  - Rejected files cleanup: every 1 hour\n"
        "  - WorkCycle jobs processor: every 2 minutes\n"
        "  - WorkCycle email jobs processor: every 1 minute\n"
        "  - WorkItem jobs processor: every 1 minute\n"
        "  - Message digests: every 6 hours\n"
        "  - Clear old notifications: weekly (Sunday 3 AM)"
    )


def run_deadline_reminders():
    """
    Wrapper job that calls the Django management command.
    Keeps all business logic out of the scheduler.
    """
    now = timezone.now()
    logger.info(f"Running scheduled deadline reminders at {now:%Y-%m-%d %H:%M:%S}")

    call_command("send_deadline_reminders")


def run_cleanup_rejected_files():
    """
    Clean up rejected files that have expired (24 hours after rejection).
    Runs hourly to ensure timely cleanup.
    """
    now = timezone.now()
    logger.info(f"Running rejected files cleanup at {now:%Y-%m-%d %H:%M:%S}")

    call_command("cleanup_rejected_files")


def run_process_workcycle_jobs():
    """
    Process pending WorkCycleJob records for async WorkCycle creation.
    Runs every 2 minutes to ensure timely processing.
    """
    now = timezone.now()
    logger.info(f"Running WorkCycle jobs processor at {now:%Y-%m-%d %H:%M:%S}")

    call_command("process_workcycle_jobs")


def run_process_workcycle_email_jobs():
    """
    Process pending WorkCycleEmailJob records for async email sending.
    Runs every 1 minute to ensure timely email delivery.
    """
    now = timezone.now()
    logger.info(f"Running WorkCycle email jobs processor at {now:%Y-%m-%d %H:%M:%S}")

    call_command("process_workcycle_email_jobs")


def run_process_workitem_jobs():
    """
    Process pending WorkItemStatusJob and WorkItemReviewJob records.
    Runs every 1 minute to ensure timely processing.
    """
    now = timezone.now()
    logger.info(f"Running WorkItem jobs processor at {now:%Y-%m-%d %H:%M:%S}")

    call_command("process_workitem_jobs")


def run_send_message_digests():
    """
    Send email digests for unread messages.
    Runs every 6 hours to keep users informed.
    """
    now = timezone.now()
    logger.info(f"Running message digests at {now:%Y-%m-%d %H:%M:%S}")

    call_command("send_message_digests")


def run_clear_message_notifications():
    """
    Clear old message notifications.
    Runs weekly on Sunday at 3 AM to keep database clean.
    """
    now = timezone.now()
    logger.info(f"Running clear message notifications at {now:%Y-%m-%d %H:%M:%S}")

    call_command("clear_message_notifications")
