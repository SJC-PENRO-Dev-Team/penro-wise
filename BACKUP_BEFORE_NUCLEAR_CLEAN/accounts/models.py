from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from structure.models import DocumentFolder
from django.core.exceptions import ValidationError, PermissionDenied

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # =====================================================
    # BASIC USER INFO
    # =====================================================
    position_title = models.CharField(
        max_length=150,
        blank=True,
        help_text="Job title or designation"
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        help_text="User profile picture"
    )
    login_role = models.CharField(
        max_length=50,
        choices=[
            ("admin", "Admin"),
            ("user", "User"),
        ],
        default="user",
        db_index=True,
    )

    # =====================================================
    # DEPARTMENT ASSIGNMENT
    # =====================================================
    department = models.ForeignKey(
        'WorkforcesDepartment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text="User's department assignment"
    )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        full_name = self.get_full_name()
        return full_name or self.username


class WorkforcesDepartment(models.Model):
    """Single unified department - no hierarchy."""
    name = models.CharField(
        max_length=200,
        default="Workforces Department",
        help_text="Department name"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional department description"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workforces Department"
        verbose_name_plural = "Workforces Departments"
        ordering = ["name"]
    
    def __str__(self):
        return self.name

# ============================================================
# 3. PLANNING (WHAT & WHEN)
# ============================================================

class WorkCycle(models.Model):
    """
    Represents a planning window for work items.

    Lifecycle is DERIVED from:
    - Admin intent (is_active)
    - Deadline proximity (due_at)

    No lifecycle state is stored in the database.
    """

    # ============================
    # LIFECYCLE STATES (DERIVED)
    # ============================
    class LifecycleState(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        DUE_SOON = "due_soon", "Due Soon"
        LAPSED = "lapsed", "Lapsed"
        ARCHIVED = "archived", "Archived"

    # ============================
    # CORE FIELDS
    # ============================
    title = models.CharField(
        max_length=200,
        help_text="Title of the task, report, or work cycle"
    )

    description = models.TextField(
        blank=True,
        help_text="Optional details or instructions"
    )

    due_at = models.DateTimeField(
        help_text="Deadline for this work cycle"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workcycles",
        help_text="User who created this work cycle"
    )

    # Admin intent
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive work cycles are hidden / archived manually"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ============================
    # DERIVED LIFECYCLE (SOURCE OF TRUTH)
    # ============================
    @property
    def lifecycle_state(self):
        """
        Determines lifecycle based on:
        1. Admin intent (is_active)
        2. Deadline proximity
        """

        # Admin override always wins
        if not self.is_active:
            return self.LifecycleState.ARCHIVED

        now = timezone.now()

        # Deadline reached or passed
        if now >= self.due_at:
            return self.LifecycleState.LAPSED

        # Due soon = within 3 days
        if (self.due_at - now) <= timedelta(days=3):
            return self.LifecycleState.DUE_SOON

        return self.LifecycleState.ONGOING

    # ============================
    # HUMAN-READABLE TIME REMAINING
    # ============================
    @property
    def time_remaining(self):
        """
        Returns remaining time in a compact human format.
        Example: '2d 4h 15m'
        """

        now = timezone.now()
        total_seconds = int((self.due_at - now).total_seconds())

        if total_seconds <= 0:
            return "Expired"

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours or days:
            parts.append(f"{hours}h")
        if minutes or hours or days:
            parts.append(f"{minutes}m")

        return " ".join(parts)

    # ============================
    # DJANGO META
    # ============================
    class Meta:
        ordering = ["-due_at"]
        indexes = [
            models.Index(fields=["due_at"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title
    
class WorkAssignment(models.Model):
    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        related_name="assignments",
        help_text="Work cycle being assigned"
    )

    assigned_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="user_assignments",
        help_text="Assign directly to a specific user"
    )

    assigned_department = models.ForeignKey(
        WorkforcesDepartment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="department_assignments",
        help_text="Assign to entire department"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(assigned_user__isnull=False) |
                    models.Q(assigned_department__isnull=False)
                ),
                name="workassignment_requires_user_or_department"
            )
        ]
        ordering = ["-assigned_at"]

    def __str__(self):
        target = self.assigned_user or self.assigned_department
        return f"{self.workcycle} → {target}"

# ============================================================
# 4. EXECUTION (THE WORK)
# ============================================================



class WorkItem(models.Model):
    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        related_name="work_items"
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="work_items"
    )

    # ======================
    # ACTIVITY / LIFECYCLE
    # ======================
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive items are archived or closed for a specific reason"
    )

    inactive_reason = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        choices=[
            ("reassigned", "Reassigned"),
            ("duplicate", "Duplicate Submission"),
            ("invalid", "Invalid / Not Required"),
            ("superseded", "Superseded by New Submission"),
            ("archived", "Archived After Completion"),
        ],
        help_text="Reason why this work item became inactive"
    )

    inactive_note = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional explanation or comment"
    )

    inactive_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this item became inactive"
    )

    inactive_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="archived_work_items",
        help_text="User who archived or deactivated this work item"
    )

    # ======================
    # STATUS / SUBMISSION
    # ======================
    status = models.CharField(
        max_length=30,
        choices=[
            ("not_started", "Not Started"),
            ("working_on_it", "Working on It"),
            ("done", "Done (Submitted)"),
        ],
        default="not_started",
        db_index=True
    )

    status_label = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)

    # ======================
    # REVIEW
    # ======================
    review_decision = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending Review"),
            ("approved", "Approved"),
            ("revision", "Needs Revision"),
        ],
        default="pending",
        db_index=True
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # ======================
    # TIMESTAMPS
    # ======================
    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workcycle", "owner")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["review_decision"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["inactive_reason"]),
            models.Index(fields=["inactive_by"]),  # ✅ helpful for audit queries
        ]

    # =====================================================
    # SAVE LOGIC (SAFE + AUDITABLE)
    # =====================================================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old = None

        if not is_new:
            old = (
                WorkItem.objects
                .filter(pk=self.pk)
                .values(
                    "is_active",
                    "review_decision",
                )
                .first()
            )

        # ---------------------
        # SUBMISSION TIMESTAMP
        # ---------------------
        if self.status == "done":
            if self.submitted_at is None:
                self.submitted_at = timezone.now()
        else:
            self.submitted_at = None

        # ---------------------
        # REVIEW TIMESTAMP
        # ---------------------
        if self.review_decision in ("approved", "revision"):
            if not old or old["review_decision"] != self.review_decision:
                self.reviewed_at = timezone.now()
        else:
            self.reviewed_at = None

        # ---------------------
        # INACTIVE AUDIT
        # ---------------------
        if not self.is_active:
            if self.inactive_at is None:
                self.inactive_at = timezone.now()
        else:
            self.inactive_at = None
            self.inactive_reason = ""
            self.inactive_note = ""
            self.inactive_by = None  # ✅ reset on reactivation

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.workcycle} — {self.owner}"


class WorkItemAttachment(models.Model):
    ATTACHMENT_TYPE_CHOICES = [
        ("matrix_a", "Matrix A"),
        ("matrix_b", "Matrix B"),
        ("mov", "MOV"),
        ("document", "Document"),  # For standalone file manager uploads
        ("admin_upload", "Admin Upload"),  # For admin file manager uploads
    ]

    work_item = models.ForeignKey(
        "accounts.WorkItem",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
        help_text="Work item this file belongs to (null for standalone file manager uploads)"
    )

    folder = models.ForeignKey(
        "structure.DocumentFolder",
        null=True,
        blank=True,
        related_name="files",
        on_delete=models.SET_NULL
    )

    attachment_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        db_index=True,
        default="document",
        help_text="Type of attachment (matrix_a, matrix_b, mov for work items; document for standalone)"
    )

    file = models.FileField(
        upload_to='work_items/',
        null=True,
        blank=True,
        help_text="Uploaded file (null for link attachments)"
    )

    link_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL for link attachments (alternative to file upload)"
    )
    
    link_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Title/name for link attachments (displayed in file manager)"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Uploader (null only for system/admin actions)"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    # ============================
    # FILE ACCEPTANCE STATUS
    # ============================
    acceptance_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending Review"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending",
        db_index=True,
        help_text="Admin acceptance status for this file"
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the file was accepted"
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the file was rejected"
    )

    rejection_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When rejected file will be auto-deleted (24h after rejection)"
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_attachments",
        help_text="Admin who accepted/rejected this file"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the file was reviewed by admin"
    )

    rejection_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional reason for rejection"
    )

    class Meta:
        indexes = [
            models.Index(fields=["attachment_type"]),
            models.Index(fields=["folder"]),
            models.Index(fields=["work_item", "folder"]),
            models.Index(fields=["acceptance_status"]),
            models.Index(fields=["rejection_expires_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["folder", "file"],
                condition=models.Q(link_url__isnull=True),  # Only apply to files, not links
                name="unique_file_per_folder"
            )
        ]

    # ============================
    # VALIDATION (FLEXIBLE)
    # ============================
    def clean(self):
        """
        Validates file/link placement with simplified organizational structure.
        
        For work item attachments:
        - Files CANNOT be in: ROOT, YEAR, CATEGORY (pure organizational containers)
        - Files CAN be in: WORKCYCLE, WORKFORCES_DEPARTMENT, ATTACHMENT
        
        For standalone file manager uploads:
        - Files can be in any folder except ROOT, YEAR, CATEGORY
        
        For link attachments:
        - Must have either file OR link_url (not both, not neither)
        - Links can be placed in any folder (no restrictions)
        """
        # Validate file vs link_url
        has_file = bool(self.file)
        has_link = bool(self.link_url)
        
        if not has_file and not has_link:
            raise ValidationError("Attachment must have either a file or a link URL.")
        
        if has_file and has_link:
            raise ValidationError("Attachment cannot have both a file and a link URL.")
        
        # Link attachments can be in any folder - no validation needed
        if has_link:
            return
        
        if not self.folder:
            return  # Allow null folder (will be auto-resolved on save for work items)

        # Import here to avoid circular dependency
        from structure.models import DocumentFolder

        # Files CANNOT be placed in pure structural folders
        invalid_folder_types = [
            DocumentFolder.FolderType.ROOT,
            DocumentFolder.FolderType.YEAR,
            DocumentFolder.FolderType.CATEGORY,  # Attachment type buckets
        ]

        if self.folder.folder_type in invalid_folder_types:
            folder_label = self.folder.get_folder_type_display()
            raise ValidationError(
                f"Files cannot be placed in {folder_label} folders. "
                f"These are organizational containers only."
            )

        # Files CAN be placed in any organizational leaf folder
        valid_folder_types = [
            DocumentFolder.FolderType.WORKCYCLE,              # Fallback/unorganized
            DocumentFolder.FolderType.WORKFORCES_DEPARTMENT,  # Department folder
            DocumentFolder.FolderType.ATTACHMENT,             # Custom subfolders
        ]

        if self.folder.folder_type not in valid_folder_types:
            raise ValidationError(
                f"Files cannot be placed in {self.folder.get_folder_type_display()} folders."
            )

        # Workcycle integrity check (only for work item attachments)
        # Ensure file's folder belongs to the same work cycle
        if self.work_item and self.folder.workcycle:
            if self.folder.workcycle != self.work_item.workcycle:
                raise ValidationError(
                    f"This folder belongs to work cycle '{self.folder.workcycle.title}' "
                    f"but the file belongs to work cycle '{self.work_item.workcycle.title}'. "
                    f"Files can only be placed in folders from the same work cycle."
                )

    # ============================
    # SAVE HOOK (AUTO-RESOLVE FOLDER)
    # ============================
    def save(self, *args, **kwargs):
        """
        Auto-resolves folder if not provided (for work item file attachments only).
        
        For work item file attachments:
        - Uses flexible organizational structure based on user's org assignment
        - Folder is auto-resolved using work_item, attachment_type, and actor
        
        For link attachments:
        - Folder must be provided (links are now folder-specific, not global)
        
        For standalone file manager uploads:
        - Folder must be provided explicitly
        - No auto-resolution (work_item is None)
        
        For admin uploads:
        - Skip validation (admins can upload anywhere)
        """
        # Auto-resolve folder if missing (only for work item file attachments)
        if not self.folder and self.work_item and self.file:
            if not self.uploaded_by:
                raise PermissionDenied(
                    "uploaded_by must be set when creating attachments."
                )

            from structure.services.folder_resolution import resolve_attachment_folder

            self.folder = resolve_attachment_folder(
                work_item=self.work_item,
                attachment_type=self.attachment_type,
                actor=self.uploaded_by
            )
        
        # For standalone uploads (no work_item), folder must be provided
        elif not self.folder and not self.work_item and self.file:
            raise ValidationError(
                "Folder is required for standalone file uploads (when work_item is not provided)."
            )
        
        # For link attachments, folder must be provided
        elif not self.folder and self.link_url:
            raise ValidationError(
                "Folder is required for link attachments."
            )

        # Skip validation for admin uploads (they can upload anywhere)
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation and self.attachment_type != 'admin_upload':
            self.full_clean()
        
        super().save(*args, **kwargs)

    # ============================
    # STRING REPRESENTATION
    # ============================
    def __str__(self):
        if self.work_item:
            return f"{self.get_attachment_type_display()} — {self.work_item}"
        else:
            return f"Standalone: {self.get_filename() or 'Unnamed file'}"

    # ============================
    # HELPERS
    # ============================
    def get_folder_path(self):
        """Returns human-readable folder path for this attachment."""
        if self.folder:
            return self.folder.get_path_string()
        return "No folder assigned"

    def get_filename(self):
        """Returns just the filename without the path."""
        if self.file:
            return self.file.name.split('/')[-1]
        elif self.link_url:
            return self.link_title or self.link_url
        return None
    
    def is_link(self):
        """Returns True if this is a link attachment."""
        return bool(self.link_url)
    
    def is_file(self):
        """Returns True if this is a file attachment."""
        return bool(self.file)
        
class WorkItemMessage(models.Model):
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="work_item_messages"
    )

    # ============================================================
    # MESSAGE META
    # ============================================================
    sender_role = models.CharField(
        max_length=50,
        choices=[
            ("admin", "Admin"),
            ("user", "User"),
        ],
        db_index=True,
        help_text="Role of the sender at the time the message was sent"
    )

    message = models.TextField(
        help_text="Message regarding status, review, or work clarification"
    )

    # ============================================================
    # OPTIONAL CONTEXT (SYSTEM / AUDIT MESSAGES)
    # ============================================================
    related_status = models.CharField(
        max_length=30,
        blank=True,
        help_text="Status this message refers to (optional)"
    )

    related_review = models.CharField(
        max_length=30,
        blank=True,
        help_text="Review decision this message refers to (optional)"
    )

    # ============================================================
    # ⚠️ LEGACY READ FIELDS (DEPRECATED)
    # DO NOT USE THESE FOR CHAT LOGIC
    # ============================================================
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="LEGACY: do not use for chat read logic"
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="LEGACY: do not use for chat read logic"
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)

    # ============================================================
    # MODEL CONFIG
    # ============================================================
    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["sender_role"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["work_item", "created_at"]),
        ]

    # ============================================================
    # SAVE OVERRIDE (LOCK ROLE AT CREATION)
    # ============================================================
    def save(self, *args, **kwargs):
        if not self.pk and not self.sender_role:
            self.sender_role = getattr(self.sender, "login_role", "user")
        super().save(*args, **kwargs)

    # ============================================================
    # STRING REPRESENTATION
    # ============================================================
    def __str__(self):
        return (
            f"[{self.created_at:%Y-%m-%d %H:%M}] "
            f"{self.sender} → WorkItem#{self.work_item_id}"
        )

    # ============================================================
    # HELPERS
    # ============================================================
    def is_system_message(self):
        return bool(self.related_status or self.related_review)

    # ============================================================
    # ✅ FACEBOOK-STYLE READ RECEIPT (CORE LOGIC)
    # ============================================================
    @classmethod
    def mark_thread_as_read(cls, *, work_item, reader):
        """
        Mark a discussion thread as read for a specific user
        using a per-user read cursor (Facebook-style).
        """

        # Get the last message NOT sent by the reader
        last_message = (
            cls.objects
            .filter(work_item=work_item)
            .exclude(sender=reader)
            .order_by("-id")
            .first()
        )

        if not last_message:
            return 0

        read_state, _ = WorkItemReadState.objects.update_or_create(
            work_item=work_item,
            user=reader,
            defaults={
                "last_read_message": last_message,
                "last_read_at": timezone.now(),
            }
        )

        # Return number of messages that were unread before marking
        return cls.objects.filter(
            work_item=work_item,
            id__gt=read_state.last_read_message_id
        ).exclude(sender=reader).count()
    
class WorkItemReadState(models.Model):
    """
    Per-user read cursor for a WorkItem discussion.
    This is the correct Facebook-style read receipt model.
    """

    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        related_name="read_states"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_item_read_states"
    )

    last_read_message = models.ForeignKey(
        WorkItemMessage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    last_read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("work_item", "user")
        indexes = [
            models.Index(fields=["work_item", "user"]),
        ]

    def __str__(self):
        return (
            f"{self.user} read up to "
            f"message {self.last_read_message_id or 'None'} "
            f"in WorkItem#{self.work_item_id}"
        )


# ============================================================
# USER ANALYTICS MODEL
# ============================================================
class UserAnalytics(models.Model):
    """
    Tracks user performance metrics for analytics dashboards.
    Updated periodically or on relevant events.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="analytics"
    )

    # ============================
    # SUBMISSION METRICS
    # ============================
    total_work_items = models.PositiveIntegerField(
        default=0,
        help_text="Total work items assigned to user"
    )

    completed_work_items = models.PositiveIntegerField(
        default=0,
        help_text="Work items marked as done"
    )

    on_time_submissions = models.PositiveIntegerField(
        default=0,
        help_text="Submissions made before deadline"
    )

    late_submissions = models.PositiveIntegerField(
        default=0,
        help_text="Submissions made after deadline"
    )

    # ============================
    # REVIEW METRICS
    # ============================
    approved_work_items = models.PositiveIntegerField(
        default=0,
        help_text="Work items approved by admin"
    )

    revision_requests = models.PositiveIntegerField(
        default=0,
        help_text="Work items sent back for revision"
    )

    # ============================
    # FILE METRICS
    # ============================
    total_files_uploaded = models.PositiveIntegerField(
        default=0,
        help_text="Total files uploaded by user"
    )

    accepted_files = models.PositiveIntegerField(
        default=0,
        help_text="Files accepted by admin"
    )

    rejected_files = models.PositiveIntegerField(
        default=0,
        help_text="Files rejected by admin"
    )

    # ============================
    # CALCULATED RATIOS (CACHED)
    # ============================
    on_time_ratio = models.FloatField(
        default=0.0,
        help_text="Percentage of on-time submissions (0-100)"
    )

    approval_ratio = models.FloatField(
        default=0.0,
        help_text="Percentage of approved work items (0-100)"
    )

    file_acceptance_ratio = models.FloatField(
        default=0.0,
        help_text="Percentage of accepted files (0-100)"
    )

    # ============================
    # TIMESTAMPS
    # ============================
    last_calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When metrics were last recalculated"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Analytics"
        verbose_name_plural = "User Analytics"

    def __str__(self):
        return f"Analytics for {self.user}"

    # ============================
    # RECALCULATE METRICS
    # ============================
    def recalculate(self):
        """
        Recalculates all metrics from source data.
        Call this after significant events or periodically.
        """
        from django.db.models import Count, Q, F

        # Work item metrics
        work_items = WorkItem.objects.filter(
            owner=self.user,
            is_active=True
        )

        self.total_work_items = work_items.count()
        self.completed_work_items = work_items.filter(status="done").count()

        # On-time vs late
        submitted_items = work_items.filter(
            status="done",
            submitted_at__isnull=False
        )

        self.on_time_submissions = submitted_items.filter(
            submitted_at__lte=F("workcycle__due_at")
        ).count()

        self.late_submissions = submitted_items.filter(
            submitted_at__gt=F("workcycle__due_at")
        ).count()

        # Review metrics
        self.approved_work_items = work_items.filter(
            review_decision="approved"
        ).count()

        self.revision_requests = work_items.filter(
            review_decision="revision"
        ).count()

        # File metrics
        attachments = WorkItemAttachment.objects.filter(
            uploaded_by=self.user
        )

        self.total_files_uploaded = attachments.count()
        self.accepted_files = attachments.filter(
            acceptance_status="accepted"
        ).count()
        self.rejected_files = attachments.filter(
            acceptance_status="rejected"
        ).count()

        # Calculate ratios
        if self.completed_work_items > 0:
            self.on_time_ratio = round(
                (self.on_time_submissions / self.completed_work_items) * 100, 1
            )
        else:
            self.on_time_ratio = 0.0

        reviewed_items = self.approved_work_items + self.revision_requests
        if reviewed_items > 0:
            self.approval_ratio = round(
                (self.approved_work_items / reviewed_items) * 100, 1
            )
        else:
            self.approval_ratio = 0.0

        reviewed_files = self.accepted_files + self.rejected_files
        if reviewed_files > 0:
            self.file_acceptance_ratio = round(
                (self.accepted_files / reviewed_files) * 100, 1
            )
        else:
            self.file_acceptance_ratio = 0.0

        self.save()

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create analytics record for a user."""
        analytics, created = cls.objects.get_or_create(user=user)
        if created:
            analytics.recalculate()
        return analytics



# ============================================================
# HIDDEN DISCUSSION MODEL
# ============================================================
class HiddenDiscussion(models.Model):
    """
    Tracks hidden discussions for users and admins.
    Users can hide individual work item discussions.
    Admins can hide by work item or by workcycle.
    """

    HIDE_TYPE_CHOICES = [
        ("work_item", "Work Item"),
        ("workcycle", "Work Cycle"),
        ("user_thread", "User Thread"),  # Admin hiding specific user's thread
    ]

    # Who hid the discussion
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hidden_discussions"
    )

    # Type of hiding
    hide_type = models.CharField(
        max_length=20,
        choices=HIDE_TYPE_CHOICES,
        default="work_item"
    )

    # The work item being hidden (for users and specific admin hides)
    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hidden_by_users"
    )

    # The workcycle being hidden (for admin bulk hide)
    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hidden_by_admins"
    )

    # The specific user whose thread is hidden (for admin)
    hidden_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="threads_hidden_by_admins"
    )

    # Timestamps
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["hidden_by", "hide_type"]),
            models.Index(fields=["hidden_by", "work_item"]),
            models.Index(fields=["hidden_by", "workcycle"]),
        ]
        # Prevent duplicate hides
        constraints = [
            models.UniqueConstraint(
                fields=["hidden_by", "work_item"],
                condition=models.Q(hide_type="work_item"),
                name="unique_hidden_work_item"
            ),
            models.UniqueConstraint(
                fields=["hidden_by", "workcycle"],
                condition=models.Q(hide_type="workcycle"),
                name="unique_hidden_workcycle"
            ),
            models.UniqueConstraint(
                fields=["hidden_by", "hidden_user", "workcycle"],
                condition=models.Q(hide_type="user_thread"),
                name="unique_hidden_user_thread"
            ),
        ]

    def __str__(self):
        if self.hide_type == "work_item":
            return f"{self.hidden_by} hid WorkItem#{self.work_item_id}"
        elif self.hide_type == "workcycle":
            return f"{self.hidden_by} hid WorkCycle#{self.workcycle_id}"
        else:
            return f"{self.hidden_by} hid {self.hidden_user}'s thread in WorkCycle#{self.workcycle_id}"

    @classmethod
    def is_hidden_for_user(cls, user, work_item):
        """Check if a work item discussion is hidden for a user."""
        return cls.objects.filter(
            hidden_by=user,
            work_item=work_item,
            hide_type="work_item"
        ).exists()

    @classmethod
    def is_hidden_for_admin(cls, admin, work_item=None, workcycle=None, target_user=None):
        """Check if a discussion is hidden for an admin."""
        # Check work item level hide
        if work_item:
            if cls.objects.filter(
                hidden_by=admin,
                work_item=work_item,
                hide_type="work_item"
            ).exists():
                return True

        # Check workcycle level hide
        if workcycle:
            if cls.objects.filter(
                hidden_by=admin,
                workcycle=workcycle,
                hide_type="workcycle"
            ).exists():
                return True

        # Check user thread level hide
        if target_user and workcycle:
            if cls.objects.filter(
                hidden_by=admin,
                hidden_user=target_user,
                workcycle=workcycle,
                hide_type="user_thread"
            ).exists():
                return True

        return False

    @classmethod
    def get_hidden_work_item_ids(cls, user):
        """Get list of work item IDs hidden by a user."""
        return list(cls.objects.filter(
            hidden_by=user,
            hide_type="work_item",
            work_item__isnull=False
        ).values_list("work_item_id", flat=True))

    @classmethod
    def get_hidden_workcycle_ids(cls, admin):
        """Get list of workcycle IDs hidden by an admin."""
        return list(cls.objects.filter(
            hidden_by=admin,
            hide_type="workcycle",
            workcycle__isnull=False
        ).values_list("workcycle_id", flat=True))


# ============================================================
# WORKCYCLE JOB MODEL (ASYNC PROCESSING)
# ============================================================
class WorkCycleJob(models.Model):
    """
    Database-backed job queue for async WorkCycle processing.
    Handles WorkItem creation and notification sending without blocking HTTP requests.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this job has been retried"
    )

    last_error = models.TextField(
        blank=True,
        help_text="Last error message if job failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Job for WorkCycle#{self.workcycle_id} - {self.status}"


# ============================================================
# WORKCYCLE EMAIL JOB MODEL (ASYNC EMAIL NOTIFICATIONS)
# ============================================================
class WorkCycleEmailJob(models.Model):
    """
    Database-backed job queue for async WorkCycle email notifications.
    Handles email sending for create/edit/reassign operations without blocking HTTP requests.
    """

    JOB_TYPE_CHOICES = [
        ("created", "Created"),
        ("edited", "Edited"),
        ("reassigned", "Reassigned"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        related_name="email_jobs"
    )

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        db_index=True,
        help_text="Type of email notification to send"
    )

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workcycle_email_jobs",
        help_text="User who performed the action"
    )

    # Store old values for comparison (JSON field would be better but keeping it simple)
    old_due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Old due date (for edited jobs)"
    )

    inactive_note = models.TextField(
        blank=True,
        help_text="Reassignment note (for reassigned jobs)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this job has been retried"
    )

    last_error = models.TextField(
        blank=True,
        help_text="Last error message if job failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["job_type", "status"]),
        ]

    def __str__(self):
        return f"Email Job ({self.job_type}) for WorkCycle#{self.workcycle_id} - {self.status}"


# ============================================================
# WORKITEM STATUS JOB MODEL (ASYNC PROCESSING)
# ============================================================
class WorkItemStatusJob(models.Model):
    """
    Database-backed job queue for async WorkItem status change notifications.
    Handles in-app notifications and email sending without blocking HTTP requests.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        related_name="status_jobs"
    )

    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workitem_status_jobs"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this job has been retried"
    )

    last_error = models.TextField(
        blank=True,
        help_text="Last error message if job failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workitem_status_jobs"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"StatusJob for WorkItem#{self.work_item_id} - {self.status}"


# ============================================================
# WORKITEM REVIEW JOB MODEL (ASYNC PROCESSING)
# ============================================================
class WorkItemReviewJob(models.Model):
    """
    Database-backed job queue for async WorkItem review notifications.
    Handles in-app notifications and email sending with detailed file statistics.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        related_name="review_jobs"
    )

    old_decision = models.CharField(max_length=30)
    new_decision = models.CharField(max_length=30)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workitem_review_jobs"
    )

    file_stats = models.JSONField(
        default=dict,
        blank=True,
        help_text="File statistics (accepted/rejected counts, file names)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this job has been retried"
    )

    last_error = models.TextField(
        blank=True,
        help_text="Last error message if job failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workitem_review_jobs"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"ReviewJob for WorkItem#{self.work_item_id} - {self.status}"
