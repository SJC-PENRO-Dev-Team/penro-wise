from django.db import models
from django.conf import settings
from django.utils import timezone

from accounts.models import WorkItem, WorkCycle


class EmailLog(models.Model):
    """
    Logs all emails sent through the system for tracking and auditing.
    Admins can view all email logs, users can only view their own.
    """
    
    class EmailType(models.TextChoices):
        WELCOME = "welcome", "Welcome Email"
        ORG_CHANGE = "org_change", "Organization Change"
        PROFILE_UPDATE = "profile_update", "Profile Update"
        PASSWORD_RESET = "password_reset", "Password Reset"
        NOTIFICATION = "notification", "Notification"
        SYSTEM = "system", "System Email"
        OTHER = "other", "Other"
    
    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        PENDING = "pending", "Pending"
    
    # Sender info
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text="User who triggered the email (null for system emails)"
    )
    sender_email = models.EmailField(
        help_text="Email address used as sender"
    )
    
    # Recipient info
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_emails",
        help_text="User who received the email (null for external recipients)"
    )
    recipient_email = models.EmailField(
        help_text="Email address of recipient"
    )
    
    # Email content
    subject = models.CharField(max_length=255)
    body_text = models.TextField(
        help_text="Plain text version of email body"
    )
    body_html = models.TextField(
        blank=True,
        help_text="HTML version of email body (optional)"
    )
    
    # Classification
    email_type = models.CharField(
        max_length=20,
        choices=EmailType.choices,
        default=EmailType.OTHER,
        db_index=True
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if email failed to send"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Read status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the recipient has read this email"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the email was marked as read"
    )
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
            models.Index(fields=["email_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["recipient", "is_read"]),
        ]
    
    def __str__(self):
        return f"{self.email_type} | {self.recipient_email} | {self.subject[:50]}"
    
    @classmethod
    def log_email(cls, recipient_email, subject, body_text, body_html="", 
                  email_type="other", sender=None, sender_email=None, 
                  recipient=None, status="pending"):
        """Create an email log entry."""
        from django.conf import settings
        
        return cls.objects.create(
            sender=sender,
            sender_email=sender_email or settings.DEFAULT_FROM_EMAIL,
            recipient=recipient,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            email_type=email_type,
            status=status
        )
    
    def mark_sent(self):
        """Mark email as successfully sent."""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at"])
    
    def mark_failed(self, error_message):
        """Mark email as failed with error message."""
        self.status = self.Status.FAILED
        self.error_message = str(error_message)
        self.save(update_fields=["status", "error_message"])
    
    def mark_as_read(self):
        """Mark email as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread emails for a user (as recipient)."""
        return cls.objects.filter(
            recipient=user,
            is_read=False,
            status=cls.Status.SENT
        ).count()


class Notification(models.Model):
    """
    A derived, user-facing notification.
    Notifications are NOT the source of truth — they reflect
    events happening in WorkItem, WorkCycle, etc.
    """

    # =====================================================
    # CATEGORY (matches your signal files 1:1)
    # =====================================================
    class Category(models.TextChoices):
        REMINDER = "reminder", "Reminder"
        STATUS = "status", "Status"
        REVIEW = "review", "Review"
        ASSIGNMENT = "assignment", "Assignment"
        MESSAGE = "message", "Message"
        SYSTEM = "system", "System"

    # =====================================================
    # SEVERITY / PRIORITY (UI + sorting)
    # =====================================================
    class Priority(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        DANGER = "danger", "Danger"

    # =====================================================
    # CORE RELATIONSHIPS
    # =====================================================
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who receives this notification"
    )

    # =====================================================
    # CLASSIFICATION
    # =====================================================
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        db_index=True
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.INFO,
        db_index=True
    )

    # =====================================================
    # CONTENT
    # =====================================================
    title = models.CharField(
        max_length=200,
        help_text="Short headline shown in notification list"
    )

    message = models.TextField(
        help_text="Detailed message shown when expanded"
    )

    # =====================================================
    # OPTIONAL CONTEXT (VERY IMPORTANT FOR GROUPING & LINKS)
    # =====================================================
    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    workcycle = models.ForeignKey(
        WorkCycle,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    # Optional: link to any page (fallback)
    action_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional URL the notification should link to"
    )

    # =====================================================
    # STATE
    # =====================================================
    is_read = models.BooleanField(
        default=False,
        db_index=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    # =====================================================
    # DJANGO META
    # =====================================================
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["category"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["recipient", "category", "is_read"]),
        ]

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================
    def __str__(self):
        return (
            f"{self.recipient} | "
            f"{self.category.upper()} | "
            f"{self.title}"
        )

    # =====================================================
    # INSTANCE HELPERS
    # =====================================================
    def mark_as_read(self):
        """Safely mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    # =====================================================
    # BULK HELPERS (IMPORTANT FOR UX)
    # =====================================================
    @classmethod
    def mark_all_as_read(cls, user, category=None):
        """
        Mark all unread notifications (optionally by category)
        as read for a user.
        """
        qs = cls.objects.filter(recipient=user, is_read=False)
        if category:
            qs = qs.filter(category=category)

        return qs.update(
            is_read=True,
            read_at=timezone.now()
        )
