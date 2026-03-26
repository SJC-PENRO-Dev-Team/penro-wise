"""
Management command to process pending WorkCycleJob records.

Usage:
    python manage.py process_workcycle_jobs

This command should be run:
- Periodically via cron/scheduler (every 1-5 minutes)
- Or manually after creating workcycles
- Or triggered by a webhook/signal

The command:
1. Finds all PENDING jobs
2. Marks them as PROCESSING
3. Calls process_workcycle_job() service
4. Updates status to DONE or FAILED
5. Logs any errors
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import logging

from accounts.models import WorkCycleJob
from admin_app.services.workcycle_service import process_workcycle_job

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending WorkCycleJob records"

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=10,
            help='Maximum number of jobs to process in one run'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retries for failed jobs'
        )

    def handle(self, *args, **options):
        max_jobs = options['max_jobs']
        max_retries = options['max_retries']

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting WorkCycleJob processor (max_jobs={max_jobs}, max_retries={max_retries})"
            )
        )

        # =====================================================
        # FIND PENDING JOBS
        # =====================================================
        pending_jobs = WorkCycleJob.objects.filter(
            status="pending"
        ).select_related("workcycle")[:max_jobs]

        if not pending_jobs:
            self.stdout.write("No pending jobs found.")
            return

        self.stdout.write(f"Found {len(pending_jobs)} pending job(s)")

        # =====================================================
        # PROCESS EACH JOB
        # =====================================================
        processed_count = 0
        failed_count = 0

        for job in pending_jobs:
            try:
                self.stdout.write(f"Processing Job#{job.id} for WorkCycle#{job.workcycle_id}...")

                # Mark as processing
                job.status = "processing"
                job.save(update_fields=["status", "updated_at"])

                # Process the job
                with transaction.atomic():
                    process_workcycle_job(job)

                # Mark as done
                job.status = "done"
                job.last_error = ""
                job.save(update_fields=["status", "last_error", "updated_at"])

                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Job#{job.id} completed successfully")
                )

            except Exception as e:
                error_msg = str(e)
                logger.exception(f"Job#{job.id} failed: {error_msg}")

                # Update job with error
                job.retry_count += 1
                job.last_error = error_msg[:1000]  # Truncate long errors

                # Mark as failed if max retries reached
                if job.retry_count >= max_retries:
                    job.status = "failed"
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Job#{job.id} failed permanently after {job.retry_count} retries"
                        )
                    )
                else:
                    job.status = "pending"  # Retry later
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠ Job#{job.id} failed (retry {job.retry_count}/{max_retries}): {error_msg}"
                        )
                    )

                job.save(update_fields=["status", "retry_count", "last_error", "updated_at"])
                failed_count += 1

        # =====================================================
        # SUMMARY
        # =====================================================
        self.stdout.write(
            self.style.SUCCESS(
                f"\nProcessing complete: {processed_count} succeeded, {failed_count} failed"
            )
        )
