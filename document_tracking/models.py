"""
Models for Digital Document Tracking System.

CRITICAL: This system is completely isolated from existing workflow systems.
DO NOT import or reference workcycle, workitem, workassignment, or workitemattachment models.
"""
from django.db import models
from django.conf import settings


class Section(models.Model):
    """
    Processing sections/departments for document routing.

    Sections represent organizational units that process documents.
    Each section can have multiple officers assigned to it.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Section/Department name (e.g., licensing, enforcement, admin)"
    )

    display_name = models.CharField(
        max_length=150,
        help_text="Display name for the section"
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description of this section's responsibilities"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Active sections appear in submission forms"
    )

    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )

    # Section Officers (Many-to-Many relationship)
    officers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='document_sections',
        blank=True,
        help_text="Users assigned as officers for this section"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Section"
        verbose_name_plural = "Sections"

    def __str__(self):
        return self.display_name or self.name

    def get_name_display(self):
        """Return display name for backward compatibility."""
        return self.display_name or self.name



class DocumentType(models.Model):
    """
    Configurable document types with custom tracking number prefixes.
    
    Each document type has a unique prefix used in tracking number generation.
    Format: PREFIX-YEAR-SERIAL (e.g., MEM-2026-001)
    """
    
    SERIAL_MODE_CHOICES = [
        ('auto', 'Auto-generate'),
        ('manual', 'Manual entry'),
        ('both', 'Both (admin chooses)'),
    ]
    
    RESET_POLICY_CHOICES = [
        ('none', 'Never reset (continuous sequence)'),
        ('monthly', 'Reset monthly'),
        ('yearly', 'Reset yearly'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Document type name (e.g., Memorandum, Letter, Report)"
    )
    
    prefix = models.CharField(
        max_length=5,
        unique=True,
        help_text="Tracking number prefix (2-5 uppercase letters, e.g., MEM, LTR, RPT)"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Optional description of this document type"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active document types appear in submission forms"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    serial_mode = models.CharField(
        max_length=10,
        choices=SERIAL_MODE_CHOICES,
        default='auto',
        help_text="How serial numbers are assigned"
    )
    
    reset_policy = models.CharField(
        max_length=10,
        choices=RESET_POLICY_CHOICES,
        default='yearly',
        help_text="When to reset the sequence counter (applies to auto mode only)"
    )
    
    reset_annually = models.BooleanField(
        default=True,
        help_text="DEPRECATED: Use reset_policy instead. Reset serial number to 1 each year"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Document Type"
        verbose_name_plural = "Document Types"
    
    def __str__(self):
        return f"{self.name} ({self.prefix})"
    
    def clean(self):
        """Validate prefix format."""
        from django.core.exceptions import ValidationError
        import re
        
        if self.prefix:
            # Convert to uppercase
            self.prefix = self.prefix.upper()
            
            # Validate format: 2-5 uppercase letters only
            if not re.match(r'^[A-Z]{2,5}$', self.prefix):
                raise ValidationError({
                    'prefix': 'Prefix must be 2-5 uppercase letters only (e.g., MEM, LTR, RPT)'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_next_serial(self, year=None, month=None):
        """
        Get the next available serial number for this document type.
        Handles reset_policy: none, monthly, yearly.
        
        Args:
            year: Year for the sequence (defaults to current year)
            month: Month for the sequence (only used if reset_policy='monthly')
        
        Returns:
            int: Next serial number
        """
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        # Determine if we need month based on reset_policy
        if self.reset_policy == 'monthly':
            if month is None:
                month = datetime.now().month
        elif self.reset_policy == 'none':
            # For continuous sequence, use a fixed year (e.g., 1)
            year = 1
            month = None
        else:  # yearly
            month = None
        
        # Get or create sequence with proper locking to prevent race conditions
        from django.db import transaction
        with transaction.atomic():
            sequence, created = TrackingNumberSequence.objects.select_for_update().get_or_create(
                document_type=self,
                year=year,
                month=month,
                defaults={'last_serial': 0}
            )
            
            sequence.last_serial += 1
            sequence.save()
            
            return sequence.last_serial
    
    def format_tracking_number(self, year, serial):
        """Format a tracking number using this document type's prefix."""
        return f"{self.prefix}-{year}-{serial:012d}"


class TrackingNumberSequence(models.Model):
    """
    Tracks the last used serial number for each document type per year.
    
    This ensures unique, sequential tracking numbers within each year.
    """
    
    document_type = models.ForeignKey(
        'DocumentType',
        on_delete=models.PROTECT,
        related_name='sequences',
        help_text="Document type this sequence belongs to"
    )
    
    year = models.IntegerField(
        help_text="Year for this sequence"
    )
    
    month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Month for monthly sequences (1-12, null for yearly/continuous)"
    )
    
    last_serial = models.IntegerField(
        default=0,
        help_text="Last serial number used"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['document_type', 'year', 'month']]
        ordering = ['-year', '-month', 'document_type']
        verbose_name = "Tracking Number Sequence"
        verbose_name_plural = "Tracking Number Sequences"
    
    def __str__(self):
        if self.month:
            return f"{self.document_type.prefix}-{self.year}-{self.month:02d}: {self.last_serial}"
        return f"{self.document_type.prefix}-{self.year}: {self.last_serial}"



class Submission(models.Model):
    """
    Core document submission record.
    
    CRITICAL: Completely independent from WorkCycle/WorkItem.
    This model represents a document submission that goes through
    a strict workflow sequence with status transitions.
    """
    
    # Document Type Choices
    DOCUMENT_TYPE_CHOICES = [
        ('permit', 'Permit'),
        ('inspection', 'Inspection'),
        ('memo', 'Memo'),
        ('others', 'Others'),
    ]
    
    # Status Choices (ONLY THESE - DO NOT ADD MORE)
    STATUS_CHOICES = [
        ('pending_tracking', 'Pending Tracking Assignment'),
        ('received', 'Received'),
        ('under_review', 'Under Review'),
        ('for_compliance', 'For Compliance'),
        ('returned_to_sender', 'Returned to Sender'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        # NOTE: 'archived' status removed - approved/rejected submissions are now stored in File Manager
    ]
    
    # ===== IDENTIFICATION =====
    tracking_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Unique tracking number (assigned by admin)"
    )
    
    # ===== SUBMISSION DATA =====
    title = models.CharField(
        max_length=255,
        help_text="Document title"
    )
    
    purpose = models.TextField(
        help_text="Purpose of the document submission"
    )
    
    # NEW: Document Type (FK to DocumentType model)
    doc_type = models.ForeignKey(
        'DocumentType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="Document type (for tracking number generation)"
    )
    
    # DEPRECATED: Old document_type field (kept for backward compatibility)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Type of document for routing"
    )
    
    # ===== WORKFLOW =====
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending_tracking',
        db_index=True,
        help_text="Current workflow status"
    )
    
    # ===== OWNERSHIP AND ROUTING =====
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='document_submissions',
        help_text="User who submitted the document"
    )
    
    assigned_section = models.ForeignKey(
        'Section',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="Section assigned to process this submission"
    )
    
    # ===== FILE STORAGE REFERENCES =====
    # Using existing file manager infrastructure
    primary_folder = models.ForeignKey(
        'structure.DocumentFolder',
        on_delete=models.PROTECT,
        related_name='primary_submissions',
        null=True,
        blank=True,
        help_text="Primary storage folder for submission files"
    )
    
    archive_folder = models.ForeignKey(
        'structure.DocumentFolder',
        on_delete=models.PROTECT,
        related_name='archived_submissions',
        null=True,
        blank=True,
        help_text="Archive storage folder for archived files (DEPRECATED - use file_manager_folder)"
    )
    
    # NEW: File Manager Integration (Phase 1)
    file_manager_folder = models.ForeignKey(
        'structure.DocumentFolder',
        on_delete=models.SET_NULL,
        related_name='tracked_submissions',
        null=True,
        blank=True,
        help_text="File Manager folder where approved submission files are stored (ROOT > Year > Submissions > Title)"
    )
    
    is_stored_in_file_manager = models.BooleanField(
        default=False,
        help_text="True if submission files have been moved to File Manager (happens on approval)"
    )
    
    # ===== LOCKING =====
    is_locked = models.BooleanField(
        default=False,
        help_text="Record is locked (read-only) after archival"
    )
    
    tracking_locked = models.BooleanField(
        default=False,
        help_text="Tracking number is locked and cannot be modified"
    )
    
    # ===== TIMESTAMPS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['submitted_by']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['document_type']),
            models.Index(fields=['assigned_section']),
        ]
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
    
    def __str__(self):
        if self.tracking_number:
            return f"{self.tracking_number} - {self.title}"
        return f"Pending - {self.title}"
    
    def save(self, *args, **kwargs):
        """
        Override save to enforce data integrity rules.
        """
        # Only validate if this is an update (not a new instance)
        if self.pk:
            old_instance = Submission.objects.get(pk=self.pk)
            
            # Prevent modification of tracking_number if it was already locked
            if old_instance.tracking_locked and old_instance.tracking_number != self.tracking_number:
                raise ValueError("Cannot modify tracking number after it has been locked")
            
            # Prevent modification of submitted_by
            if old_instance.submitted_by != self.submitted_by:
                raise ValueError("Cannot modify submitted_by field")
            
            # Prevent any modifications if record was already locked
            if old_instance.is_locked and old_instance.status != self.status:
                raise ValueError("Cannot modify archived submission")
        
        super().save(*args, **kwargs)



class Logbook(models.Model):
    """
    Append-only audit trail for all submission actions.
    
    CRITICAL: This is an append-only log. Never delete or modify existing entries.
    All actions on submissions must create a logbook entry.
    """
    
    ACTION_CHOICES = [
        ('created', 'Submission Created'),
        ('tracking_assigned', 'Tracking Assigned'),
        ('status_changed', 'Status Changed'),
        ('files_uploaded', 'Files Uploaded'),
        ('archived', 'Archived'),
        ('reset_to_start', 'Reset to Start'),
        ('undo_action', 'Undo Action'),
        ('workflow_reverted', 'Workflow Reverted'),
        ('section_assigned', 'Section Assigned'),
    ]
    
    submission = models.ForeignKey(
        'Submission',
        on_delete=models.PROTECT,
        related_name='logs',
        help_text="Submission this log entry belongs to"
    )
    
    action = models.CharField(
        max_length=100,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    
    # ===== ACTION DETAILS =====
    old_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Previous status (for status_changed action)"
    )
    
    new_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="New status (for status_changed action)"
    )
    
    remarks = models.TextField(
        blank=True,
        help_text="Additional remarks or notes"
    )
    
    file_names = models.TextField(
        blank=True,
        help_text="JSON list of file names (for files_uploaded action)"
    )
    
    # ===== ACTOR =====
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        help_text="User who performed the action"
    )
    
    # ===== TIMESTAMP =====
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was performed"
    )
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['submission', 'timestamp']),
            models.Index(fields=['action']),
        ]
        verbose_name = "Logbook Entry"
        verbose_name_plural = "Logbook Entries"
    
    def __str__(self):
        return f"{self.submission} - {self.get_action_display()} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """
        Override save to prevent modifications to existing entries.
        """
        if self.pk:
            raise ValueError("Cannot modify existing logbook entries (append-only)")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion of logbook entries.
        """
        raise ValueError("Cannot delete logbook entries (append-only)")
