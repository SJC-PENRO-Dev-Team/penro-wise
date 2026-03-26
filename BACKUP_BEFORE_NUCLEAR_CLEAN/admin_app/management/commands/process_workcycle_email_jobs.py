"""
Management command to process pending WorkCycleEmailJob records.

Usage:
    python manage.py process_workcycle_email_jobs

This command should be run:
- Periodically via APScheduler (every 1-2 minutes)
- Or manually after workcycle operations

The command:
1. Finds all PENDING email jobs
2. Marks them as PROCESSING
3. Sends appropriate emails based on job_type
4. Updates status to DONE or FAILED
5. Logs any errors
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

from accounts.models import WorkCycleEmailJob, User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending WorkCycleEmailJob records"

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=20,
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
                f"Starting WorkCycleEmailJob processor (max_jobs={max_jobs}, max_retries={max_retries})"
            )
        )

        # =====================================================
        # FIND PENDING JOBS
        # =====================================================
        pending_jobs = WorkCycleEmailJob.objects.filter(
            status="pending"
        ).select_related("workcycle", "actor")[:max_jobs]

        if not pending_jobs:
            self.stdout.write("No pending email jobs found.")
            return

        self.stdout.write(f"Found {len(pending_jobs)} pending email job(s)")

        # =====================================================
        # PROCESS EACH JOB
        # =====================================================
        processed_count = 0
        failed_count = 0

        for job in pending_jobs:
            try:
                self.stdout.write(f"Processing EmailJob#{job.id} ({job.job_type}) for WorkCycle#{job.workcycle_id}...")

                # Mark as processing
                job.status = "processing"
                job.save(update_fields=["status", "updated_at"])

                # Send emails based on job type
                if job.job_type == "created":
                    self._send_created_emails(job)
                elif job.job_type == "edited":
                    self._send_edited_emails(job)
                elif job.job_type == "reassigned":
                    self._send_reassigned_emails(job)

                # Mark as done
                job.status = "done"
                job.last_error = ""
                job.save(update_fields=["status", "last_error", "updated_at"])

                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ EmailJob#{job.id} completed successfully")
                )

            except Exception as e:
                error_msg = str(e)
                logger.exception(f"EmailJob#{job.id} failed: {error_msg}")

                # Update job with error
                job.retry_count += 1
                job.last_error = error_msg[:1000]  # Truncate long errors

                # Mark as failed if max retries reached
                if job.retry_count >= max_retries:
                    job.status = "failed"
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ EmailJob#{job.id} failed permanently after {job.retry_count} retries"
                        )
                    )
                else:
                    job.status = "pending"  # Retry later
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠ EmailJob#{job.id} failed (retry {job.retry_count}/{max_retries}): {error_msg}"
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

    def _send_created_emails(self, job):
        """Send emails for workcycle creation."""
        workcycle = job.workcycle
        actor = job.actor

        # Email content
        subject = "New Work Cycle Assigned"
        
        actor_name = (
            actor.get_full_name()
            if actor and actor.get_full_name()
            else getattr(actor, "username", "System")
        )

        body = (
            f"Good day.\n\n"
            f"You have been assigned a new work cycle:\n\n"
            f"Title: {workcycle.title}\n"
            f"Description: {workcycle.description or 'N/A'}\n"
            f"Due Date: {workcycle.due_at:%A, %d %B %Y at %I:%M %p}\n\n"
            f"Assigned by: {actor_name}\n"
            f"Date assigned: {timezone.localtime():%A, %d %B %Y}\n\n"
            f"Please log in to the system to view details and submit your work.\n\n"
            f"— PENRO WISE System"
        )

        # Get recipients (assigned users)
        user_ids = (
            workcycle.work_items
            .filter(is_active=True)
            .values_list("owner_id", flat=True)
            .distinct()
        )

        recipients = User.objects.filter(
            id__in=user_ids,
            is_active=True,
            email__isnull=False
        ).exclude(email="")

        # Send emails
        for user in recipients:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,  # Raise exception on failure
            )

        # Also send to creator (admin)
        if workcycle.created_by and workcycle.created_by.email:
            admin_body = (
                f"Good day.\n\n"
                f"You have successfully created a new work cycle:\n\n"
                f"Title: {workcycle.title}\n"
                f"Description: {workcycle.description or 'N/A'}\n"
                f"Due Date: {workcycle.due_at:%A, %d %B %Y at %I:%M %p}\n"
                f"Assigned Users: {recipients.count()}\n\n"
                f"Date created: {timezone.localtime():%A, %d %B %Y}\n\n"
                f"— PENRO WISE System"
            )
            
            send_mail(
                subject="Work Cycle Created Successfully",
                message=admin_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[workcycle.created_by.email],
                fail_silently=False,
            )

    def _send_edited_emails(self, job):
        """Send emails for workcycle edit."""
        workcycle = job.workcycle
        actor = job.actor
        old_due_at = job.old_due_at

        # Build change summary
        changes = []
        if old_due_at and old_due_at != workcycle.due_at:
            changes.append(
                f"Due date changed from "
                f"{old_due_at:%d %B %Y} to {workcycle.due_at:%d %B %Y}"
            )

        if not changes:
            changes.append("Work cycle details were updated")

        change_summary = "; ".join(changes)

        # Email content
        subject = "Notice: Work Cycle Updated"
        
        actor_name = (
            actor.get_full_name()
            if actor and actor.get_full_name()
            else getattr(actor, "username", "System")
        )

        body = (
            f"Good day.\n\n"
            f"This is to inform you that the work cycle "
            f"\"{workcycle.title}\" has been updated.\n\n"
            f"Summary of changes:\n"
            f"- {change_summary}\n\n"
            f"Updated by: {actor_name}\n"
            f"Date of update: {timezone.localtime():%A, %d %B %Y}\n\n"
            f"This notice is issued for your information.\n\n"
            f"— PENRO WISE System"
        )

        # Get recipients (assigned users)
        user_ids = (
            workcycle.work_items
            .filter(is_active=True)
            .values_list("owner_id", flat=True)
            .distinct()
        )

        recipients = User.objects.filter(
            id__in=user_ids,
            is_active=True,
            email__isnull=False
        ).exclude(email="")

        # Send emails
        for user in recipients:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        # Also send to creator (admin)
        if workcycle.created_by and workcycle.created_by.email:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[workcycle.created_by.email],
                fail_silently=False,
            )

    def _send_reassigned_emails(self, job):
        """Send emails for workcycle reassignment."""
        workcycle = job.workcycle
        actor = job.actor
        inactive_note = job.inactive_note

        # Email content for NEW assignees
        subject_new = "New Work Cycle Assigned"
        
        actor_name = (
            actor.get_full_name()
            if actor and actor.get_full_name()
            else getattr(actor, "username", "System")
        )

        body_new = (
            f"Good day.\n\n"
            f"You have been assigned to a work cycle:\n\n"
            f"Title: {workcycle.title}\n"
            f"Description: {workcycle.description or 'N/A'}\n"
            f"Due Date: {workcycle.due_at:%A, %d %B %Y at %I:%M %p}\n\n"
            f"Reassignment Note: {inactive_note or 'N/A'}\n\n"
            f"Reassigned by: {actor_name}\n"
            f"Date reassigned: {timezone.localtime():%A, %d %B %Y}\n\n"
            f"Please log in to the system to view details and submit your work.\n\n"
            f"— PENRO WISE System"
        )

        # Email content for REMOVED assignees
        subject_removed = "Work Cycle Reassignment Notice"
        
        body_removed = (
            f"Good day.\n\n"
            f"This is to inform you that you have been removed from the work cycle:\n\n"
            f"Title: {workcycle.title}\n\n"
            f"Reason: {inactive_note or 'Reassigned to other personnel'}\n\n"
            f"Reassigned by: {actor_name}\n"
            f"Date: {timezone.localtime():%A, %d %B %Y}\n\n"
            f"If you have questions, please contact your administrator.\n\n"
            f"— PENRO WISE System"
        )

        # Get NEW assignees (active work items)
        new_user_ids = (
            workcycle.work_items
            .filter(is_active=True)
            .values_list("owner_id", flat=True)
            .distinct()
        )

        new_recipients = User.objects.filter(
            id__in=new_user_ids,
            is_active=True,
            email__isnull=False
        ).exclude(email="")

        # Send emails to new assignees
        for user in new_recipients:
            send_mail(
                subject=subject_new,
                message=body_new,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        # Get REMOVED assignees (inactive work items with reassigned reason)
        removed_user_ids = (
            workcycle.work_items
            .filter(is_active=False, inactive_reason="reassigned")
            .values_list("owner_id", flat=True)
            .distinct()
        )

        removed_recipients = User.objects.filter(
            id__in=removed_user_ids,
            is_active=True,
            email__isnull=False
        ).exclude(email="")

        # Send emails to removed assignees
        for user in removed_recipients:
            send_mail(
                subject=subject_removed,
                message=body_removed,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
