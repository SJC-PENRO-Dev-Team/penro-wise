"""
Business logic services for Digital Document Tracking System.

This module contains service classes that handle:
- File storage operations (FileService)
- Tracking number generation and assignment (TrackingService)
- Status transitions and validation (StatusService)
- Document routing (RoutingService)
- Archival processes (ArchivalService)

CRITICAL: This system is completely isolated from existing workflow systems.
Uses existing file manager infrastructure (DocumentFolder, WorkItemAttachment) but
does NOT import or reference workcycle/workitem business logic.
"""
import re
import os
from datetime import datetime
from typing import List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.text import slugify

from structure.models import DocumentFolder
from accounts.models import WorkItemAttachment, User
from .models import Submission, Section, Logbook


class FileService:
    """
    Handles file storage operations using existing file manager infrastructure.
    
    Uses DocumentFolder and WorkItemAttachment models for file storage,
    but operates independently from workcycle/workitem logic.
    """
    
    @staticmethod
    def sanitize_folder_name(title: str) -> str:
        """
        Convert title to safe folder name.
        
        Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Remove special characters (keep alphanumeric, hyphens, underscores)
        - Limit length to 100 characters
        - Remove leading/trailing underscores
        
        Args:
            title: Original submission title
            
        Returns:
            Sanitized folder name safe for filesystem
            
        Example:
            "Tree Cutting Permit (2024)" -> "tree_cutting_permit_2024"
        """
        if not title:
            return "untitled"
        
        # Use Django's slugify for basic sanitization
        sanitized = slugify(title)
        
        # Replace hyphens with underscores for consistency
        sanitized = sanitized.replace('-', '_')
        
        # Remove any remaining special characters
        sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:100]
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure not empty
        if not sanitized:
            sanitized = "untitled"
        
        return sanitized
    
    @staticmethod
    def create_primary_folder(submission: Submission) -> DocumentFolder:
        """
        Create folder for primary document storage.
        Creates under: ROOT > YEAR > CATEGORY > submission folder
        
        Args:
            submission: Submission instance
            
        Returns:
            DocumentFolder instance for primary storage
            
        Raises:
            ValueError: If submission has no title
        """
        if not submission.title:
            raise ValueError("Submission must have a title")
        
        # Get or create document tracking root folder
        doc_root, _ = DocumentFolder.objects.get_or_create(
            name="Document Tracking",
            folder_type=DocumentFolder.FolderType.ROOT,
            defaults={
                'parent': None,
                'is_system_generated': True,
            }
        )
        
        # Get or create year folder under root
        year = datetime.now().year
        year_folder, _ = DocumentFolder.objects.get_or_create(
            name=str(year),
            folder_type=DocumentFolder.FolderType.YEAR,
            parent=doc_root,
            defaults={
                'is_system_generated': True,
            }
        )
        
        # Get or create category folder under year
        category_folder, _ = DocumentFolder.objects.get_or_create(
            name="Submissions",
            folder_type=DocumentFolder.FolderType.CATEGORY,
            parent=year_folder,
            defaults={
                'is_system_generated': True,
            }
        )
        
        sanitized_title = FileService.sanitize_folder_name(submission.title)
        
        # Get submitter name for folder
        submitter_name = submission.submitted_by.get_full_name() or submission.submitted_by.email.split('@')[0]
        sanitized_submitter = FileService.sanitize_folder_name(submitter_name)
        
        # Create unique folder name with submitter and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{sanitized_title}_{sanitized_submitter}_{timestamp}"
        
        # Create the folder under category (manual folder under system hierarchy)
        folder = DocumentFolder.objects.create(
            name=folder_name,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            parent=category_folder,
            created_by=submission.submitted_by,
            is_system_generated=False,
        )
        
        return folder
    
    @staticmethod
    def create_archive_folder(submission: Submission) -> DocumentFolder:
        """
        Create folder for archived document storage.
        Creates under: ROOT > YEAR > CATEGORY > Archive > submission folder
        
        Args:
            submission: Submission instance with tracking_number
            
        Returns:
            DocumentFolder instance for archive storage
            
        Raises:
            ValueError: If submission has no tracking number
        """
        if not submission.tracking_number:
            raise ValueError("Submission must have a tracking number for archival")
        
        # Get or create document tracking root folder
        doc_root, _ = DocumentFolder.objects.get_or_create(
            name="Document Tracking",
            folder_type=DocumentFolder.FolderType.ROOT,
            defaults={
                'parent': None,
                'is_system_generated': True,
            }
        )
        
        # Get or create year folder under root
        year = datetime.now().year
        year_folder, _ = DocumentFolder.objects.get_or_create(
            name=str(year),
            folder_type=DocumentFolder.FolderType.YEAR,
            parent=doc_root,
            defaults={
                'is_system_generated': True,
            }
        )
        
        # Get or create category folder under year
        category_folder, _ = DocumentFolder.objects.get_or_create(
            name="Archive",
            folder_type=DocumentFolder.FolderType.CATEGORY,
            parent=year_folder,
            defaults={
                'is_system_generated': True,
            }
        )
        
        # Get submitter name for folder
        submitter_name = submission.submitted_by.get_full_name() or submission.submitted_by.email.split('@')[0]
        sanitized_submitter = FileService.sanitize_folder_name(submitter_name)
        
        # Create unique archive folder name with submitter
        folder_name = f"archive_{submission.tracking_number}_{sanitized_submitter}"
        
        # Create the folder under category
        folder = DocumentFolder.objects.create(
            name=folder_name,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            parent=category_folder,
            created_by=submission.submitted_by,
            is_system_generated=False,
        )
        
        return folder
    
    @staticmethod
    def store_files(
        submission: Submission,
        files: List[UploadedFile],
        folder: DocumentFolder,
        uploaded_by: User
    ) -> List[WorkItemAttachment]:
        """
        Store files in specified folder using WorkItemAttachment.
        
        Args:
            submission: Submission instance
            files: List of uploaded files
            folder: DocumentFolder to store files in
            uploaded_by: User uploading the files
            
        Returns:
            List of created WorkItemAttachment instances
            
        Note:
            Uses WorkItemAttachment model but does NOT link to WorkItem.
            The work_item field will be None for document tracking files.
            Uses 'document' attachment_type for standalone uploads.
        """
        attachments = []
        
        for uploaded_file in files:
            # Create attachment - WorkItemAttachment will handle file storage
            # No need to check for duplicates as the model has unique constraint
            attachment = WorkItemAttachment.objects.create(
                work_item=None,  # Not linked to WorkItem (standalone)
                folder=folder,
                file=uploaded_file,
                uploaded_by=uploaded_by,
                attachment_type='document',  # Standalone document upload
                acceptance_status='accepted',  # Auto-accept for document tracking
            )
            
            attachments.append(attachment)
        
        return attachments
    
    @staticmethod
    def move_files_to_archive(submission: Submission) -> None:
        """
        Move all files from primary_folder to archive_folder.
        
        Args:
            submission: Submission instance with both folders set
            
        Raises:
            ValueError: If folders are not set
        """
        if not submission.primary_folder:
            raise ValueError("Submission has no primary folder")
        
        if not submission.archive_folder:
            raise ValueError("Submission has no archive folder")
        
        # Get all files in primary folder
        files = WorkItemAttachment.objects.filter(
            folder=submission.primary_folder
        )
        
        # Move files to archive folder
        files.update(folder=submission.archive_folder)



class FileManagerService:
    """
    Handles File Manager integration for approved submissions.
    
    When a submission is approved, this service:
    1. Creates folder structure: ROOT > YEAR > Submissions > [Title]
    2. Moves files from primary_folder to File Manager folder
    3. Adds submission type badge to folder
    4. Locks the submission
    """
    
    @staticmethod
    def get_or_create_root_folder() -> DocumentFolder:
        """
        Get or create the ROOT folder for File Manager.
        
        Returns:
            DocumentFolder instance with folder_type=ROOT
        """
        root_folder, created = DocumentFolder.objects.get_or_create(
            name="ROOT",
            folder_type=DocumentFolder.FolderType.ROOT,
            defaults={
                'parent': None,
                'is_system_generated': True,
            }
        )
        return root_folder
    
    @staticmethod
    def get_or_create_year_folder(year: int) -> DocumentFolder:
        """
        Get or create the year folder under ROOT.
        
        Args:
            year: Year number (e.g., 2026)
            
        Returns:
            DocumentFolder instance for the year
        """
        root_folder = FileManagerService.get_or_create_root_folder()
        
        year_folder, created = DocumentFolder.objects.get_or_create(
            name=str(year),
            folder_type=DocumentFolder.FolderType.YEAR,
            parent=root_folder,
            defaults={
                'is_system_generated': True,
            }
        )
        return year_folder
    
    @staticmethod
    def get_or_create_submissions_folder(year_folder: DocumentFolder) -> DocumentFolder:
        """
        Get or create the Submissions folder under year.
        
        Args:
            year_folder: Parent year folder
            
        Returns:
            DocumentFolder instance for Submissions category
        """
        submissions_folder, created = DocumentFolder.objects.get_or_create(
            name="Submissions",
            folder_type=DocumentFolder.FolderType.CATEGORY,
            parent=year_folder,
            defaults={
                'is_system_generated': True,
            }
        )
        return submissions_folder
    
    @staticmethod
    def get_or_create_section_folder(
        submissions_folder: DocumentFolder,
        section: Section
    ) -> DocumentFolder:
        """
        Get or create the section folder under Submissions.
        
        Args:
            submissions_folder: Parent Submissions folder
            section: Section instance
            
        Returns:
            DocumentFolder instance for the section (blue system folder)
        """
        section_name = section.get_name_display()  # Get display name (e.g., "Licensing", "Enforcement", "Admin")
        
        # Use ATTACHMENT type with is_system_generated=True for blue folder color
        # CATEGORY is now allowed as parent for ATTACHMENT folders (updated in structure/models.py)
        section_folder, created = DocumentFolder.objects.get_or_create(
            name=section_name,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            parent=submissions_folder,
            defaults={
                'is_system_generated': True,  # System-generated for blue color
            }
        )
        return section_folder
    
    @staticmethod
    def create_submission_folder(
        section_folder: DocumentFolder,
        submission: Submission
    ) -> DocumentFolder:
        """
        Create folder for specific submission.
        
        Folder name format: [Submission Title]
        
        Args:
            section_folder: Parent section folder
            submission: Submission instance
            
        Returns:
            DocumentFolder instance for the submission
            
        Raises:
            ValueError: If submission has no title
        """
        if not submission.title:
            raise ValueError("Submission must have a title")
        
        # Use submission title as folder name (no sanitization needed for display)
        folder_name = submission.title
        
        # Create the folder under section
        folder = DocumentFolder.objects.create(
            name=folder_name,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            parent=section_folder,
            created_by=submission.submitted_by,
            is_system_generated=False,  # User submission, not system-generated
        )
        
        return folder
    
    @staticmethod
    def move_files_to_file_manager(
        submission: Submission,
        target_folder: DocumentFolder
    ) -> int:
        """
        Move all files from primary_folder to File Manager folder.
        
        Args:
            submission: Submission instance with primary_folder
            target_folder: Destination folder in File Manager
            
        Returns:
            Number of files moved
            
        Raises:
            ValueError: If submission has no primary folder
        """
        if not submission.primary_folder:
            raise ValueError("Submission has no primary folder")
        
        # Get all files in primary folder
        files = WorkItemAttachment.objects.filter(
            folder=submission.primary_folder
        )
        
        # Count files before moving
        file_count = files.count()
        
        # Move files to File Manager folder and ensure they're accepted
        files.update(
            folder=target_folder,
            acceptance_status='accepted'  # Ensure files are visible in File Manager
        )
        
        return file_count
    
    @staticmethod
    @transaction.atomic
    def store_approved_submission(submission: Submission) -> DocumentFolder:
        """
        Store approved submission in File Manager.
        
        This is the main method that orchestrates the entire process:
        1. Create folder structure: ROOT > YEAR > Submissions > [Section] > [Title]
        2. Move files from primary_folder to new folder
        3. Update submission record
        4. Lock submission
        5. Create logbook entry
        
        Args:
            submission: Submission instance (must be approved)
            
        Returns:
            DocumentFolder instance where files are stored
            
        Raises:
            ValueError: If submission is not approved or already stored
        """
        if submission.status != 'approved':
            raise ValueError("Only approved submissions can be stored in File Manager")
        
        if submission.is_stored_in_file_manager:
            raise ValueError("Submission is already stored in File Manager")
        
        if not submission.primary_folder:
            raise ValueError("Submission has no files to store (no primary folder)")
        
        if not submission.assigned_section:
            raise ValueError("Submission must have an assigned section")
        
        # Get current year
        year = datetime.now().year
        
        # 1. Create folder structure: ROOT > YEAR > Submissions > Section > Title
        year_folder = FileManagerService.get_or_create_year_folder(year)
        submissions_folder = FileManagerService.get_or_create_submissions_folder(year_folder)
        section_folder = FileManagerService.get_or_create_section_folder(submissions_folder, submission.assigned_section)
        submission_folder = FileManagerService.create_submission_folder(section_folder, submission)
        
        # 2. Move files to File Manager
        file_count = FileManagerService.move_files_to_file_manager(submission, submission_folder)
        
        # 3. Update submission record
        submission.file_manager_folder = submission_folder
        submission.is_stored_in_file_manager = True
        submission.is_locked = True
        submission.save()
        
        # Note: Logbook entry is created by the calling method (change_status)
        # with file storage information included in remarks
        
        return submission_folder


class TrackingService:
    """
    Handles tracking number assignment and validation.
    
    Supports two modes:
    - Mode A: Auto-generate (PENRO-YYYY-XXXXX format)
    - Mode B: Manual entry (admin provides custom number)
    """
    
    @staticmethod
    def generate_tracking_number(year: Optional[int] = None) -> str:
        """
        Generate tracking number in format: PENRO-YYYY-XXXXX
        
        XXXXX is 5-digit zero-padded increment unique per year.
        
        Args:
            year: Year for tracking number (defaults to current year)
            
        Returns:
            Generated tracking number (e.g., "PENRO-2026-00001")
            
        Example:
            First submission of 2026: "PENRO-2026-00001"
            Second submission of 2026: "PENRO-2026-00002"
        """
        if year is None:
            year = datetime.now().year
        
        # Find the highest tracking number for this year
        prefix = f"PENRO-{year}-"
        
        last_submission = Submission.objects.filter(
            tracking_number__startswith=prefix
        ).order_by('-tracking_number').first()
        
        if last_submission and last_submission.tracking_number:
            # Extract the increment from last tracking number
            try:
                last_increment = int(last_submission.tracking_number.split('-')[-1])
                next_increment = last_increment + 1
            except (ValueError, IndexError):
                # If parsing fails, start from 1
                next_increment = 1
        else:
            # First tracking number for this year
            next_increment = 1
        
        # Format: PENRO-YYYY-XXXXX (5-digit zero-padded)
        tracking_number = f"{prefix}{next_increment:05d}"
        
        return tracking_number
    
    @staticmethod
    def validate_tracking_number(tracking_number: str) -> bool:
        """
        Validate tracking number uniqueness.
        
        Args:
            tracking_number: Tracking number to validate
            
        Returns:
            True if unique, False if duplicate
        """
        return not Submission.objects.filter(
            tracking_number=tracking_number
        ).exists()
    
    @staticmethod
    @transaction.atomic
    def assign_tracking_number(
        submission: Submission,
        mode: str,
        manual_number: Optional[str] = None,
        actor: Optional[User] = None
    ) -> None:
        """
        Assign tracking number (Mode A: auto, Mode B: manual).
        
        Creates logbook entry and transitions status to 'received'.
        
        Args:
            submission: Submission to assign tracking number to
            mode: 'auto' or 'manual'
            manual_number: Required for manual mode
            actor: User performing the action
            
        Raises:
            ValueError: If validation fails or duplicate tracking number
        """
        if submission.tracking_locked:
            raise ValueError("Tracking number is already locked")
        
        if mode == 'auto':
            # Mode A: Auto-generate
            tracking_number = TrackingService.generate_tracking_number()
        elif mode == 'manual':
            # Mode B: Manual entry
            if not manual_number:
                raise ValueError("Manual tracking number is required for manual mode")
            
            # Validate uniqueness
            if not TrackingService.validate_tracking_number(manual_number):
                raise ValueError(f"Tracking number '{manual_number}' already exists")
            
            tracking_number = manual_number
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'auto' or 'manual'")
        
        # Assign tracking number
        submission.tracking_number = tracking_number
        submission.tracking_locked = True
        submission.status = 'received'
        submission.save()
        
        # Create logbook entry
        Logbook.objects.create(
            submission=submission,
            action='tracking_assigned',
            remarks=f"Tracking number assigned: {tracking_number} (mode: {mode})",
            actor=actor or submission.submitted_by
        )
from .workflow import StatusWorkflow


class StatusService:
    """
    Handles status transitions with validation.
    
    Enforces strict status transition matrix using StatusWorkflow.
    """
    
    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed.
        
        Args:
            current_status: Current submission status
            new_status: Desired new status
            
        Returns:
            True if transition is allowed, False otherwise
        """
        return StatusWorkflow.can_transition(current_status, new_status)
    
    @staticmethod
    def get_next_statuses(current_status: str) -> list:
        """
        Get list of valid next statuses.
        
        Args:
            current_status: Current submission status
            
        Returns:
            List of valid next status codes
        """
        return StatusWorkflow.get_next_statuses(current_status)
    
    @staticmethod
    def get_status_actions(current_status: str) -> list:
        """
        Get available status actions with labels and descriptions.
        
        Args:
            current_status: Current submission status
            
        Returns:
            List of action dictionaries
        """
        return StatusWorkflow.get_status_actions(current_status)
    
    @staticmethod
    @transaction.atomic
    def change_status(
        submission: Submission,
        new_status: str,
        actor: User,
        remarks: str = ""
    ) -> None:
        """
        Change submission status with validation and logging.
        
        Args:
            submission: Submission to update
            new_status: New status value
            actor: User performing the action
            remarks: Optional remarks for the change
            
        Raises:
            ValueError: If transition is not allowed or submission is locked
        """
        if submission.is_locked:
            raise ValueError("Cannot change status of locked submission")
        
        # NEW: Validate section assignment before approval
        if new_status == 'approved' and not submission.assigned_section:
            raise ValueError(
                "Cannot approve submission without department assignment. "
                "Please assign a department/section first."
            )
        
        # Validate transition using workflow
        if not StatusWorkflow.can_transition(submission.status, new_status):
            current_label = StatusWorkflow.get_status_info(submission.status).get('label', submission.status)
            new_label = StatusWorkflow.get_status_info(new_status).get('label', new_status)
            raise ValueError(
                f"Invalid status transition from '{current_label}' to '{new_label}'. "
                f"Please follow the workflow sequence."
            )
        
        old_status = submission.status
        submission.status = new_status
        submission.save()
        
        # NEW: If approved, store in File Manager automatically (if files exist)
        if new_status == 'approved':
            # Only attempt to store if submission has files
            if submission.primary_folder:
                try:
                    file_manager_folder = FileManagerService.store_approved_submission(submission)
                    # Add file storage info to remarks
                    storage_info = f"Files stored in File Manager: {file_manager_folder.get_path_string()}"
                    remarks = f"{storage_info}. {remarks}" if remarks else storage_info
                except Exception as e:
                    # Log the error but don't fail the status change
                    # The submission is still approved, just not stored yet
                    Logbook.objects.create(
                        submission=submission,
                        action='status_changed',
                        old_status=old_status,
                        new_status=new_status,
                        remarks=f"[ERROR] Failed to store in File Manager: {str(e)}. {remarks}",
                        actor=actor
                    )
                    raise  # Re-raise to rollback transaction
            else:
                # No files to store - submission has only links or no attachments
                # Mark as approved without file storage
                submission.is_locked = True
                submission.save()
                remarks = f"Approved without file storage (no files uploaded). {remarks}" if remarks else "Approved without file storage (no files uploaded)"
        
        # Create logbook entry for status change
        Logbook.objects.create(
            submission=submission,
            action='status_changed',
            old_status=old_status,
            new_status=new_status,
            remarks=remarks,
            actor=actor
        )
    
    @staticmethod
    @transaction.atomic
    def reset_to_start(
        submission: Submission,
        actor: User,
        remarks: str = ""
    ) -> None:
        """
        Reset submission back to initial state (pending_tracking).
        Available from Step 2 onwards.
        
        Args:
            submission: Submission to reset
            actor: User performing the reset
            remarks: Required remarks explaining why reset is needed
            
        Raises:
            ValueError: If submission is at Step 1 or remarks are missing
        """
        if submission.status == 'pending_tracking':
            raise ValueError("Cannot reset submission that is already at initial state")
        
        if not remarks or len(remarks.strip()) < 10:
            raise ValueError("Remarks are required (minimum 10 characters) to explain why this reset is necessary")
        
        old_status = submission.status
        
        # Unlock the submission if locked
        if submission.is_locked:
            submission.is_locked = False
        
        # Reset to initial state
        submission.status = 'pending_tracking'
        
        # Clear tracking lock if needed (allow reassignment)
        submission.tracking_locked = False
        
        submission.save()
        
        # Create logbook entry with special action
        Logbook.objects.create(
            submission=submission,
            action='reset_to_start',
            old_status=old_status,
            new_status='pending_tracking',
            remarks=f"[ADMIN RESET] {remarks}",
            actor=actor
        )
    
    @staticmethod
    @transaction.atomic
    def undo_last_action(
        submission: Submission,
        actor: User,
        remarks: str = ""
    ) -> None:
        """
        Undo the last status change by reverting to previous status.
        
        Args:
            submission: Submission to undo
            actor: User performing the undo
            remarks: Optional remarks explaining the undo
            
        Raises:
            ValueError: If there's no previous status to undo to
        """
        from .workflow import StatusWorkflow
        
        # Get workflow path
        workflow_path = StatusWorkflow.get_workflow_path(submission)
        
        # Get previous status
        previous_status = StatusWorkflow.get_previous_status(submission.status, workflow_path)
        
        if not previous_status:
            raise ValueError("Cannot undo - no previous status found in workflow history")
        
        if submission.status == 'pending_tracking':
            raise ValueError("Cannot undo from initial state")
        
        old_status = submission.status
        
        # Unlock if locked
        if submission.is_locked:
            submission.is_locked = False
        
        # Revert to previous status
        submission.status = previous_status
        submission.save()
        
        # Create logbook entry
        Logbook.objects.create(
            submission=submission,
            action='undo_action',
            old_status=old_status,
            new_status=previous_status,
            remarks=f"[UNDO] Reverted from {old_status} to {previous_status}. {remarks}",
            actor=actor
        )




class RoutingService:
    """
    Handles automatic document routing based on document type.
    """
    
    # Routing Map (document_type -> section_name)
    ROUTING_MAP = {
        'permit': 'licensing',
        'inspection': 'enforcement',
        'memo': 'admin',
        'others': 'admin',
    }
    
    @staticmethod
    def route_submission(submission: Submission) -> Section:
        """
        Route submission to appropriate section based on document_type.
        
        Args:
            submission: Submission to route
            
        Returns:
            Section assigned to the submission
            
        Raises:
            ValueError: If document type is invalid or section doesn't exist
        """
        section_name = RoutingService.ROUTING_MAP.get(submission.document_type)
        
        if not section_name:
            raise ValueError(f"Invalid document type: {submission.document_type}")
        
        try:
            section = Section.objects.get(name=section_name)
        except Section.DoesNotExist:
            raise ValueError(f"Section '{section_name}' does not exist")
        
        submission.assigned_section = section
        submission.save()
        
        return section
    
    @staticmethod
    @transaction.atomic
    def override_routing(
        submission: Submission,
        section: Section,
        actor: User
    ) -> None:
        """
        Allow admin to manually override routing.
        
        Args:
            submission: Submission to re-route
            section: New section to assign
            actor: User performing the override
        """
        old_section = submission.assigned_section
        submission.assigned_section = section
        submission.save()
        
        # Create logbook entry
        old_section_name = old_section.get_name_display() if old_section else "None"
        new_section_name = section.get_name_display()
        
        Logbook.objects.create(
            submission=submission,
            action='status_changed',  # Using status_changed for routing override
            remarks=f"Routing overridden: {old_section_name} → {new_section_name}",
            actor=actor
        )


