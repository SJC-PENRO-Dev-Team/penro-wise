"""
Email Service for Document Tracking System
Uses existing PENRO WISE email templates.
"""
import logging

logger = logging.getLogger(__name__)


class DocumentTrackingEmailService:
    """Service for sending document tracking emails"""
    
    @staticmethod
    def send_submission_acknowledgment(submission):
        """Send acknowledgment email after document submission"""
        # Import here to avoid circular imports
        from notifications.services.email_service import (
            send_logged_email,
            get_styled_email_html,
            format_info_box
        )
        
        recipient_email = submission.submitted_by.email
        
        if not recipient_email:
            logger.warning(f"No email for user {submission.submitted_by.username}")
            return None
        
        subject = f"Document Submission Received - {submission.title}"
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Dear <strong>{submission.submitted_by.get_full_name() or submission.submitted_by.username}</strong>,
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Your document submission has been received successfully and is now being processed.
            </p>
            
            {format_info_box("Document Title", submission.title, "📄")}
            {format_info_box("Document Type", submission.get_document_type_display(), "📋")}
            {format_info_box("Submission Date", submission.created_at.strftime('%B %d, %Y at %I:%M %p'), "📅")}
            {format_info_box("Current Status", "Pending Tracking Assignment", "⏳")}
            
            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    <strong>⏱️ Expected Processing Time:</strong> 3-5 business days
                </p>
            </div>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 20px 0 0 0;">
                A tracking number will be assigned by our admin team shortly.
            </p>
        """
        
        body_text = f"""Dear {submission.submitted_by.get_full_name() or submission.submitted_by.username},

Your document submission has been received successfully.

- Title: {submission.title}
- Document Type: {submission.get_document_type_display()}
- Submission Date: {submission.created_at.strftime('%B %d, %Y at %I:%M %p')}
- Status: Pending Tracking Assignment

Expected Processing Time: 3-5 business days

Best regards,
PENRO Document Tracking Team"""
        
        body_html = get_styled_email_html(
            title="Document Submission Received",
            content_html=content_html,
            footer_text="PENRO Document Tracking Team",
            action_url="/documents/my-submissions/",
            action_text="View My Submissions"
        )
        
        try:
            return send_logged_email(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                email_type="document_submission",
                recipient=submission.submitted_by,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send acknowledgment email: {str(e)}")
            return None
    
    @staticmethod
    def send_tracking_assigned(submission):
        """Send email when tracking number is assigned"""
        # Import here to avoid circular imports
        from notifications.services.email_service import (
            send_logged_email,
            get_styled_email_html,
            format_info_box
        )
        
        recipient_email = submission.submitted_by.email
        
        if not recipient_email:
            return None
        
        subject = f"Tracking Number Assigned - {submission.tracking_number}"
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Dear <strong>{submission.submitted_by.get_full_name() or submission.submitted_by.username}</strong>,
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Great news! Your document submission has been assigned a tracking number.
            </p>
            
            <div style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 24px; border-radius: 8px; text-align: center; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: rgba(255,255,255,0.9); font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">
                    YOUR TRACKING NUMBER
                </p>
                <p style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold; letter-spacing: 2px;">
                    {submission.tracking_number}
                </p>
            </div>
            
            {format_info_box("Document Title", submission.title, "📄")}
            {format_info_box("Document Type", submission.doc_type.name if submission.doc_type else submission.get_document_type_display(), "📋")}
            {format_info_box("Assigned Section", submission.assigned_section.get_name_display() if submission.assigned_section else 'Not assigned', "🏢")}
            {format_info_box("Current Status", submission.get_status_display(), "📊")}
        """
        
        body_text = f"""Dear {submission.submitted_by.get_full_name() or submission.submitted_by.username},

Your document submission has been assigned a tracking number.

TRACKING NUMBER: {submission.tracking_number}

- Title: {submission.title}
- Document Type: {submission.doc_type.name if submission.doc_type else submission.get_document_type_display()}
- Assigned Section: {submission.assigned_section.get_name_display() if submission.assigned_section else 'Not assigned'}

Best regards,
PENRO Document Tracking Team"""
        
        body_html = get_styled_email_html(
            title="Tracking Number Assigned",
            content_html=content_html,
            footer_text="PENRO Document Tracking Team",
            action_url="/documents/my-submissions/",
            action_text="View My Submissions"
        )
        
        try:
            return send_logged_email(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                email_type="tracking_assigned",
                recipient=submission.submitted_by,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send tracking email: {str(e)}")
            return None
    
    @staticmethod
    def send_status_change_notification(submission, old_status, new_status, remarks=""):
        """Send email when submission status changes"""
        # Import here to avoid circular imports
        from notifications.services.email_service import (
            send_logged_email,
            get_styled_email_html,
            format_info_box
        )
        
        recipient_email = submission.submitted_by.email
        
        if not recipient_email:
            return None
        
        status_dict = dict(submission._meta.get_field('status').choices)
        old_status_display = status_dict.get(old_status, old_status)
        new_status_display = status_dict.get(new_status, new_status)
        
        subject = f"Status Update - {submission.tracking_number or submission.title}"
        
        status_info = {
            'received': {'color': '#3b82f6', 'icon': '✅'},
            'under_review': {'color': '#3b82f6', 'icon': '🔍'},
            'for_compliance': {'color': '#eab308', 'icon': '⚠️'},
            'returned_to_sender': {'color': '#f59e0b', 'icon': '↩️'},
            'approved': {'color': '#22c55e', 'icon': '✅'},
            'rejected': {'color': '#ef4444', 'icon': '❌'},
            'archived': {'color': '#6b7280', 'icon': '📦'}
        }
        status_data = status_info.get(new_status, {'color': '#6b7280', 'icon': '📊'})
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Dear <strong>{submission.submitted_by.get_full_name() or submission.submitted_by.username}</strong>,
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                The status of your document submission has been updated.
            </p>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 24px 0; text-align: center;">
                <span style="background-color: #e5e7eb; color: #6b7280; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 14px;">
                    {old_status_display}
                </span>
                <span style="color: #6b7280; font-size: 20px; margin: 0 12px;">→</span>
                <span style="background-color: {status_data['color']}; color: #ffffff; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 14px;">
                    {status_data['icon']} {new_status_display}
                </span>
            </div>
            
            {format_info_box("Tracking Number", submission.tracking_number or 'Not assigned yet', "🔢")}
            {format_info_box("Document Title", submission.title, "📄")}
        """
        
        if remarks:
            content_html += f"""
            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0 0 8px 0; color: #92400e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                    💬 REMARKS
                </p>
                <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.6;">
                    {remarks}
                </p>
            </div>
            """
        
        body_text = f"""Dear {submission.submitted_by.get_full_name() or submission.submitted_by.username},

The status of your document submission has been updated.

Tracking Number: {submission.tracking_number or 'Not assigned yet'}
Title: {submission.title}

Status Change: {old_status_display} → {new_status_display}

{f'Remarks: {remarks}' if remarks else ''}

Best regards,
PENRO Document Tracking Team"""
        
        body_html = get_styled_email_html(
            title="Status Update",
            content_html=content_html,
            footer_text="PENRO Document Tracking Team",
            action_url="/documents/my-submissions/",
            action_text="View My Submissions"
        )
        
        try:
            return send_logged_email(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                email_type="status_change",
                recipient=submission.submitted_by,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send status change email: {str(e)}")
            return None
