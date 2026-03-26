"""
Service functions for processing WorkItem background jobs.

Handles:
- Status change notifications (user submissions)
- Review notifications (admin reviews)
"""

import logging
from django.db import transaction

from accounts.models import WorkItemStatusJob, WorkItemReviewJob
from notifications.services.status import notify_work_item_status_changed
from notifications.services.review import notify_work_item_review_changed

logger = logging.getLogger(__name__)


def process_workitem_status_job(job: WorkItemStatusJob):
    """
    Process a single WorkItem status change job.
    
    Handles:
    - In-app notifications
    - Email notifications (Brevo SMTP)
    
    Args:
        job: WorkItemStatusJob instance
    """
    try:
        work_item = job.work_item
        actor = job.actor
        
        if not actor:
            raise ValueError("Actor is required for status change notifications")
        
        # Call the notification service (handles both in-app and email)
        notify_work_item_status_changed(
            work_item=work_item,
            actor=actor,
            old_status=job.old_status,
        )
        
        logger.info(
            f"✅ Processed status job {job.id} for WorkItem {work_item.id} "
            f"({job.old_status} → {job.new_status})"
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to process status job {job.id}: {str(e)}",
            exc_info=True
        )
        raise


def process_workitem_review_job(job: WorkItemReviewJob):
    """
    Process a single WorkItem review job.
    
    Handles:
    - In-app notifications
    - Email notifications with detailed file statistics
    
    Args:
        job: WorkItemReviewJob instance
    """
    try:
        work_item = job.work_item
        reviewed_by = job.reviewed_by
        
        if not reviewed_by:
            raise ValueError("Reviewed_by is required for review notifications")
        
        # Call the notification service (handles both in-app and email)
        # Note: The current service doesn't use file_stats yet, but we're
        # passing the job so it can be extended in the future
        notify_work_item_review_changed(
            work_item=work_item,
            actor=reviewed_by,
            old_decision=job.old_decision,
        )
        
        logger.info(
            f"✅ Processed review job {job.id} for WorkItem {work_item.id} "
            f"({job.old_decision} → {job.new_decision})"
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to process review job {job.id}: {str(e)}",
            exc_info=True
        )
        raise
