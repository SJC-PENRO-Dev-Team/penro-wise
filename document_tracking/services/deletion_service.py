"""
Deletion Service for Document Tracking System

Handles secure deletion of rejected submissions with all related data.
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


def delete_rejected_submission(submission, actor):
    """
    Permanently delete a rejected submission and all related data.
    
    SECURITY: Only submissions with status='rejected' can be deleted.
    
    Args:
        submission: Submission instance to delete
        actor: User performing the deletion (for audit trail)
    
    Returns:
        dict: {'success': bool, 'message': str, 'deleted_files': int}
    
    Raises:
        ValidationError: If submission cannot be deleted
        PermissionDenied: If actor lacks permission
    """
    from document_tracking.models import Submission, Logbook
    from accounts.models import WorkItemAttachment
    
    # CRITICAL: Validate status
    if submission.status != 'rejected':
        raise ValidationError(
            f"Cannot delete submission with status '{submission.get_status_display()}'. "
            f"Only rejected submissions can be deleted."
        )
    
    # Validate actor has admin permission
    if not actor.login_role == 'admin':
        raise PermissionDenied("Only administrators can delete submissions")
    
    deleted_files_count = 0
    deleted_links_count = 0
    submission_title = submission.title
    submission_id = submission.id
    tracking_number = submission.tracking_number or "No tracking number"
    
    try:
        with transaction.atomic():
            # Step 1: Create final logbook entry BEFORE deletion
            Logbook.objects.create(
                submission=submission,
                action='deleted',
                remarks=f"Submission permanently deleted by {actor.get_full_name()}. "
                        f"Status was 'rejected'. All files and links removed.",
                actor=actor
            )
            
            # Step 2: Delete files from storage and database
            folders_to_check = [
                submission.primary_folder,
                submission.archive_folder,
                submission.file_manager_folder
            ]
            
            for folder in folders_to_check:
                if folder:
                    attachments = folder.files.all()
                    for attachment in attachments:
                        if attachment.link_url:
                            # It's a link - just count it
                            deleted_links_count += 1
                        else:
                            # It's a file - delete from storage
                            if attachment.file:
                                file_path = attachment.file.path if hasattr(attachment.file, 'path') else None
                                
                                # Delete physical file
                                if file_path and os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                        deleted_files_count += 1
                                        logger.info(f"Deleted file: {file_path}")
                                    except OSError as e:
                                        logger.warning(f"Could not delete file {file_path}: {e}")
                                        # Continue anyway - file might already be gone
                                else:
                                    logger.warning(f"File not found: {file_path}")
                        
                        # Delete attachment record
                        attachment.delete()
            
            # Step 3: Clear folder references from submission (to avoid PROTECT constraint)
            submission.primary_folder = None
            submission.archive_folder = None
            submission.file_manager_folder = None
            submission.save()
            
            # Step 4: Now delete the folders
            for folder in folders_to_check:
                if folder:
                    folder.delete()
            
            # Step 5: Delete all logbook entries
            logbook_count = submission.logs.count()
            submission.logs.all().delete()
            
            # Step 6: Delete the submission itself
            submission.delete()
            
            logger.info(
                f"Successfully deleted submission #{submission_id} '{submission_title}' "
                f"by {actor.get_full_name()}. "
                f"Deleted: {deleted_files_count} files, {deleted_links_count} links, "
                f"{logbook_count} log entries."
            )
            
            return {
                'success': True,
                'message': (
                    f'Submission "{submission_title}" ({tracking_number}) '
                    f'permanently deleted. '
                    f'Removed {deleted_files_count} file(s), {deleted_links_count} link(s), '
                    f'and {logbook_count} log entries.'
                ),
                'deleted_files': deleted_files_count,
                'deleted_links': deleted_links_count,
                'deleted_logs': logbook_count
            }
    
    except Exception as e:
        logger.error(
            f"Error deleting submission #{submission_id}: {str(e)}",
            exc_info=True
        )
        raise ValidationError(f"Failed to delete submission: {str(e)}")


def can_delete_submission(submission, user):
    """
    Check if a submission can be deleted by a user.
    
    Args:
        submission: Submission instance
        user: User attempting deletion
    
    Returns:
        dict: {'can_delete': bool, 'reason': str}
    """
    # Check user permission
    if user.login_role != 'admin':
        return {
            'can_delete': False,
            'reason': 'Only administrators can delete submissions'
        }
    
    # Check submission status
    if submission.status != 'rejected':
        return {
            'can_delete': False,
            'reason': f'Cannot delete submission with status "{submission.get_status_display()}". Only rejected submissions can be deleted.'
        }
    
    return {
        'can_delete': True,
        'reason': 'Submission can be deleted'
    }
