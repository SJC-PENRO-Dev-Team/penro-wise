"""
Django management command to process WorkItem background jobs.

Processes:
- WorkItemStatusJob (user submissions)
- WorkItemReviewJob (admin reviews)

Usage:
    python manage.py process_workitem_jobs

Scheduled via APScheduler to run every 1-2 minutes.
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import WorkItemStatusJob, WorkItemReviewJob
from user_app.services.workitem_job_service import (
    process_workitem_status_job,
    process_workitem_review_job,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending WorkItem status and review jobs"

    def handle(self, *args, **options):
        """
        Process all pending WorkItem jobs.
        
        Handles both status change and review jobs with:
        - Retry logic (max 3 attempts)
        - Error logging
        - Status tracking
        """
        
        status_processed = 0
        status_failed = 0
        review_processed = 0
        review_failed = 0
        
        # ============================================================
        # PROCESS STATUS JOBS
        # ============================================================
        status_jobs = WorkItemStatusJob.objects.filter(
            status="pending"
        ).select_related("work_item", "actor")[:50]  # Process in batches
        
        for job in status_jobs:
            try:
                # Mark as processing
                job.status = "processing"
                job.save(update_fields=["status", "updated_at"])
                
                # Process the job
                process_workitem_status_job(job)
                
                # Mark as done
                job.status = "done"
                job.save(update_fields=["status", "updated_at"])
                
                status_processed += 1
                
            except Exception as e:
                job.retry_count += 1
                job.last_error = str(e)[:500]  # Truncate long errors
                
                # Max 3 retries
                if job.retry_count >= 3:
                    job.status = "failed"
                    logger.error(
                        f"❌ Status job {job.id} failed after 3 attempts: {str(e)}"
                    )
                else:
                    job.status = "pending"  # Retry
                    logger.warning(
                        f"⚠️ Status job {job.id} failed (attempt {job.retry_count}/3): {str(e)}"
                    )
                
                job.save(update_fields=["status", "retry_count", "last_error", "updated_at"])
                status_failed += 1
        
        # ============================================================
        # PROCESS REVIEW JOBS
        # ============================================================
        review_jobs = WorkItemReviewJob.objects.filter(
            status="pending"
        ).select_related("work_item", "reviewed_by")[:50]  # Process in batches
        
        for job in review_jobs:
            try:
                # Mark as processing
                job.status = "processing"
                job.save(update_fields=["status", "updated_at"])
                
                # Process the job
                process_workitem_review_job(job)
                
                # Mark as done
                job.status = "done"
                job.save(update_fields=["status", "updated_at"])
                
                review_processed += 1
                
            except Exception as e:
                job.retry_count += 1
                job.last_error = str(e)[:500]  # Truncate long errors
                
                # Max 3 retries
                if job.retry_count >= 3:
                    job.status = "failed"
                    logger.error(
                        f"❌ Review job {job.id} failed after 3 attempts: {str(e)}"
                    )
                else:
                    job.status = "pending"  # Retry
                    logger.warning(
                        f"⚠️ Review job {job.id} failed (attempt {job.retry_count}/3): {str(e)}"
                    )
                
                job.save(update_fields=["status", "retry_count", "last_error", "updated_at"])
                review_failed += 1
        
        # ============================================================
        # SUMMARY
        # ============================================================
        if status_processed > 0 or review_processed > 0 or status_failed > 0 or review_failed > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Processed {status_processed} status jobs, {review_processed} review jobs"
                )
            )
            if status_failed > 0 or review_failed > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Failed: {status_failed} status jobs, {review_failed} review jobs"
                    )
                )
        else:
            self.stdout.write("No pending jobs to process")
