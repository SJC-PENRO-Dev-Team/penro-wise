"""
User Management Notification Service

Handles notifications for:
1. New user account creation (onboarding complete)
2. Organization changes (onboarding complete after reassignment)
3. Profile updates (admin editing user, user editing own profile)

Channels:
- In-app notification
- Gmail SMTP email (with logging)

Author: System
"""

from django.conf import settings
from django.urls import reverse
from notifications.models import Notification, EmailLog
from notifications.services.email_service import (
    send_logged_email, 
    get_styled_email_html, 
    format_info_box,
    format_list_items
)
from accounts.models import User


def notify_user_account_created(user, created_by_admin):
    """
    Send notification when a new user account is created.
    
    Args:
        user: The newly created User instance
        created_by_admin: The admin User who created the account
    """
    
    # Get department info
    department_name = user.department.name if user.department else "No department assigned"
    
    # Create in-app notification
    # Determine action URL based on recipient role
    if user.login_role == 'admin':
        action_url = f"/admin/users/{user.id}/"
    else:
        action_url = "/user/profile/"
    
    Notification.objects.create(
        recipient=user,
        category=Notification.Category.SYSTEM,
        priority=Notification.Priority.INFO,
        title="Welcome to PENRO WISE!",
        message=(
            f"Your account has been created by {created_by_admin.get_full_name() or created_by_admin.username}. "
            f"You have been assigned to: {department_name}. "
            f"You can now log in and start using the system."
        ),
        action_url=action_url
    )
    
    # Send email notification
    if user.email:
        admin_name = created_by_admin.get_full_name() or created_by_admin.username
        user_name = user.get_full_name() or user.username
        
        # Plain text version
        email_subject = "Welcome to PENRO WISE - Your Account is Ready"
        email_body_text = f"""Good day, {user_name}!

Congratulations! Your account has been successfully created in the PENRO WISE Work Submission & Tracking Information System.

Account Details:
- Username: {user.username}
- Email: {user.email}
- Position: {user.position_title or 'Not specified'}

Department Assignment:
{department_name}

Your account was created by: {admin_name}

You can now log in to the system using your credentials.

If you have any questions or need assistance, please contact your administrator.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE Team
"""
        
        # HTML version
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>! 🎉
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Congratulations! Your account has been successfully created in the 
                <strong>PENRO WISE Work Submission & Tracking Information System</strong>.
            </p>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                📋 Account Details
            </h3>
            {format_info_box("Username", user.username, "👤")}
            {format_info_box("Email", user.email, "📧")}
            {format_info_box("Position", user.position_title or 'Not specified', "💼")}
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                🏢 Department Assignment
            </h3>
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 16px 20px; border-radius: 8px; margin: 12px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 15px; font-weight: 500;">
                    {department_name}
                </p>
            </div>
            
            <p style="color: #64748b; font-size: 14px; margin: 20px 0 0 0;">
                Your account was created by: <strong>{admin_name}</strong>
            </p>
            
            <div style="text-align: center; margin: 32px 0;">
                <p style="color: #475569; font-size: 14px; margin: 0 0 16px 0;">
                    You can now log in to the system using your credentials.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html("Welcome to PENRO WISE! 🎉", content_html)
        
        send_logged_email(
            recipient_email=user.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="welcome",
            sender=created_by_admin,
            recipient=user,
            fail_silently=True
        )


def notify_user_department_changed(user, changed_by_admin, is_new_assignment):
    """
    Send notification when a user's department is changed.
    
    Args:
        user: The User whose department was changed
        changed_by_admin: The admin User who made the change
        is_new_assignment: Boolean indicating if this is a new assignment
    """
    
    # Get department info
    department_name = user.department.name if user.department else "No department"
    
    # Create in-app notification
    action_text = "assigned to" if is_new_assignment else "reassigned to"
    
    # Determine action URL based on recipient role
    if user.login_role == 'admin':
        action_url = f"/admin/users/{user.id}/"
    else:
        action_url = "/user/profile/"
    
    Notification.objects.create(
        recipient=user,
        category=Notification.Category.SYSTEM,
        priority=Notification.Priority.INFO,
        title=f"Department {'Assignment' if is_new_assignment else 'Update'}",
        message=(
            f"You have been {action_text} a new department by "
            f"{changed_by_admin.get_full_name() or changed_by_admin.username}: {department_name}"
        ),
        action_url=action_url
    )
    
    # Send email notification
    if user.email:
        admin_name = changed_by_admin.get_full_name() or changed_by_admin.username
        user_name = user.get_full_name() or user.username
        
        title = f"Department {'Assignment' if is_new_assignment else 'Update'}"
        
        # Plain text version
        email_subject = f"{title} - PENRO WISE"
        email_body_text = f"""Good day, {user_name}!

Your department assignment has been {'set' if is_new_assignment else 'updated'} in the PENRO WISE system.

New Department Assignment:
{department_name}

This change was made by: {admin_name}

You can view your updated profile in the system.

If you have any questions about this change, please contact your administrator.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE Team
"""
        
        # HTML version
        icon = "🆕" if is_new_assignment else "🔄"
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your department assignment has been <strong>{'set' if is_new_assignment else 'updated'}</strong> 
                in the PENRO WISE system.
            </p>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                🏢 New Department Assignment
            </h3>
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 16px 20px; border-radius: 8px; margin: 12px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 15px; font-weight: 500;">
                    {department_name}
                </p>
            </div>
            
            <p style="color: #64748b; font-size: 14px; margin: 20px 0 0 0;">
                This change was made by: <strong>{admin_name}</strong>
            </p>
            
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    💡 <strong>Note:</strong> If you have any questions about this change, please contact your administrator.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html(f"{icon} {title}", content_html)
        
        send_logged_email(
            recipient_email=user.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="dept_change",
            sender=changed_by_admin,
            recipient=user,
            fail_silently=True
        )


def notify_admins_user_profile_updated(user, updated_by_user, changed_fields):
    """
    Notify all admins when a user updates their own profile.
    
    Args:
        user: The User who updated their profile
        updated_by_user: Same as user (for consistency)
        changed_fields: Dict of field names and their new values
    """
    
    # Get all admin users
    admins = User.objects.filter(login_role='admin', is_active=True)
    
    if not admins.exists():
        return
    
    # Build changed fields summary
    field_labels = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'username': 'Username',
        'position_title': 'Position Title',
    }
    
    changes_list = []
    for field, value in changed_fields.items():
        label = field_labels.get(field, field.replace('_', ' ').title())
        changes_list.append(f"{label}: {value}")
    
    # Create in-app notifications for each admin
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            category=Notification.Category.SYSTEM,
            priority=Notification.Priority.INFO,
            title=f"User Profile Updated: {user.get_full_name() or user.username}",
            message=(
                f"{user.get_full_name() or user.username} has updated their profile. "
                f"Changed fields: {', '.join(changed_fields.keys())}"
            ),
            action_url=f"/admin/users/{user.id}/"
        )
    
    # Send email to admins
    admin_emails = [admin.email for admin in admins if admin.email]
    
    if admin_emails:
        user_name = user.get_full_name() or user.username
        
        # Plain text version
        email_subject = f"User Profile Updated: {user_name}"
        changes_text = "\n".join([f"- {item}" for item in changes_list])
        email_body_text = f"""Good day,

A user has updated their profile information in the PENRO WISE system.

User: {user_name} (@{user.username})
Email: {user.email}
Position: {user.position_title or 'Not specified'}

Updated Fields:
{changes_text}

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE System
"""
        
        # HTML version
        changes_html = "".join([format_info_box(item.split(":")[0], item.split(":")[1].strip() if ":" in item else item, "✏️") for item in changes_list])
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                A user has updated their profile information in the PENRO WISE system.
            </p>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                👤 User Information
            </h3>
            {format_info_box("Name", user_name, "👤")}
            {format_info_box("Username", f"@{user.username}", "🔑")}
            {format_info_box("Email", user.email, "📧")}
            {format_info_box("Position", user.position_title or 'Not specified', "💼")}
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                📝 Updated Fields
            </h3>
            {changes_html}
        """
        
        email_body_html = get_styled_email_html("👤 User Profile Updated", content_html)
        
        # Send to each admin individually for proper logging
        for admin in admins:
            if admin.email:
                send_logged_email(
                    recipient_email=admin.email,
                    subject=email_subject,
                    body_text=email_body_text,
                    body_html=email_body_html,
                    email_type="profile_update",
                    sender=user,
                    recipient=admin,
                    fail_silently=True
                )


def notify_user_profile_updated_by_admin(user, updated_by_admin, changed_fields):
    """
    Notify a user when an admin updates their profile.
    
    Args:
        user: The User whose profile was updated
        updated_by_admin: The admin User who made the update
        changed_fields: Dict of field names and their new values
    """
    
    # Build changed fields summary
    field_labels = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'username': 'Username',
        'position_title': 'Position Title',
        'login_role': 'Role',
        'is_active': 'Account Status',
    }
    
    changes_list = []
    for field, value in changed_fields.items():
        label = field_labels.get(field, field.replace('_', ' ').title())
        # Format boolean values
        if isinstance(value, bool):
            value = 'Active' if value else 'Inactive'
        changes_list.append(f"{label}: {value}")
    
    # Create in-app notification
    # Determine action URL based on recipient role
    if user.login_role == 'admin':
        action_url = f"/admin/users/{user.id}/"
    else:
        action_url = "/user/profile/"
    
    Notification.objects.create(
        recipient=user,
        category=Notification.Category.SYSTEM,
        priority=Notification.Priority.INFO,
        title="Your Profile Has Been Updated",
        message=(
            f"An administrator ({updated_by_admin.get_full_name() or updated_by_admin.username}) "
            f"has updated your profile. Changed fields: {', '.join(changed_fields.keys())}"
        ),
        action_url=action_url
    )
    
    # Send email notification
    if user.email:
        admin_name = updated_by_admin.get_full_name() or updated_by_admin.username
        user_name = user.get_full_name() or user.username
        
        # Plain text version
        email_subject = "Your Profile Has Been Updated - PENRO WISE"
        changes_text = "\n".join([f"- {item}" for item in changes_list])
        email_body_text = f"""Good day, {user_name}!

Your profile information has been updated by an administrator in the PENRO WISE system.

Updated by: {admin_name}

Updated Fields:
{changes_text}

If you have any questions about these changes, please contact your administrator.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE Team
"""
        
        # HTML version
        changes_html = "".join([format_info_box(item.split(":")[0], item.split(":")[1].strip() if ":" in item else item, "✏️") for item in changes_list])
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your profile information has been updated by an administrator in the PENRO WISE system.
            </p>
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 0 0 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    👤 Updated by: <strong>{admin_name}</strong>
                </p>
            </div>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                📝 Updated Fields
            </h3>
            {changes_html}
            
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    💡 <strong>Note:</strong> If you have any questions about these changes, please contact your administrator.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html("📝 Your Profile Has Been Updated", content_html)
        
        send_logged_email(
            recipient_email=user.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="profile_update",
            sender=updated_by_admin,
            recipient=user,
            fail_silently=True
        )


def notify_user_password_reset_by_admin(user, reset_by_admin):
    """
    Notify a user when an admin resets their password.
    
    Args:
        user: The User whose password was reset
        reset_by_admin: The admin User who reset the password
    """
    
    # Create in-app notification
    # Determine action URL based on recipient role
    if user.login_role == 'admin':
        action_url = f"/admin/users/{user.id}/"
    else:
        action_url = "/user/profile/"
    
    Notification.objects.create(
        recipient=user,
        category=Notification.Category.SYSTEM,
        priority=Notification.Priority.HIGH,
        title="Your Password Has Been Reset",
        message=(
            f"An administrator ({reset_by_admin.get_full_name() or reset_by_admin.username}) "
            f"has reset your password. Please use your new password to log in."
        ),
        action_url=action_url
    )
    
    # Send email notification
    if user.email:
        admin_name = reset_by_admin.get_full_name() or reset_by_admin.username
        user_name = user.get_full_name() or user.username
        
        # Plain text version
        email_subject = "Your Password Has Been Reset - PENRO WISE"
        email_body_text = f"""Good day, {user_name}!

Your password has been reset by an administrator in the PENRO WISE system.

Reset by: {admin_name}

IMPORTANT: Please use your new password to log in to the system. For security reasons, we recommend changing your password after logging in.

If you did not request this password reset or have any concerns, please contact your administrator immediately.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE Team
"""
        
        # HTML version
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your password has been reset by an administrator in the PENRO WISE system.
            </p>
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 0 0 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    👤 Reset by: <strong>{admin_name}</strong>
                </p>
            </div>
            
            <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px; font-weight: 600;">
                    🔒 IMPORTANT SECURITY NOTICE
                </p>
                <p style="margin: 0; color: #7f1d1d; font-size: 14px; line-height: 1.5;">
                    Please use your new password to log in to the system. For security reasons, we recommend changing your password after logging in.
                </p>
            </div>
            
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    💡 <strong>Note:</strong> If you did not request this password reset or have any concerns, please contact your administrator immediately.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html("🔒 Your Password Has Been Reset", content_html)
        
        send_logged_email(
            recipient_email=user.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="password_reset",
            sender=reset_by_admin,
            recipient=user,
            fail_silently=True
        )


def notify_user_password_changed(user):
    """
    Notify a user when they change their own password.
    
    Args:
        user: The User who changed their password
    """
    
    # Create in-app notification
    # Determine action URL based on user role
    if user.login_role == 'admin':
        action_url = f"/admin/users/{user.id}/"
    else:
        action_url = "/user/profile/"
    
    Notification.objects.create(
        recipient=user,
        category=Notification.Category.SYSTEM,
        priority=Notification.Priority.INFO,
        title="Password Changed Successfully",
        message="Your password has been changed successfully. If you did not make this change, please contact an administrator immediately.",
        action_url=action_url
    )
    
    # Send email notification
    if user.email:
        user_name = user.get_full_name() or user.username
        
        # Plain text version
        email_subject = "Password Changed Successfully - PENRO WISE"
        email_body_text = f"""Good day, {user_name}!

Your password has been changed successfully in the PENRO WISE system.

If you made this change, no further action is required.

If you did NOT make this change, please contact an administrator immediately and secure your account.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE Team
"""
        
        # HTML version
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your password has been changed successfully in the PENRO WISE system.
            </p>
            
            <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; color: #166534; font-size: 14px;">
                    ✅ If you made this change, no further action is required.
                </p>
            </div>
            
            <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px; font-weight: 600;">
                    🔒 SECURITY ALERT
                </p>
                <p style="margin: 0; color: #7f1d1d; font-size: 14px; line-height: 1.5;">
                    If you did NOT make this change, please contact an administrator immediately and secure your account.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html("🔒 Password Changed Successfully", content_html)
        
        send_logged_email(
            recipient_email=user.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="password_change",
            sender=user,
            recipient=user,
            fail_silently=True
        )


def notify_admins_user_password_changed(user):
    """
    Notify all admins when a user changes their own password.
    
    Args:
        user: The User who changed their password
    """
    
    # Get all admin users
    admins = User.objects.filter(login_role='admin', is_active=True)
    
    if not admins.exists():
        return
    
    user_name = user.get_full_name() or user.username
    
    # Create in-app notifications for each admin
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            category=Notification.Category.SYSTEM,
            priority=Notification.Priority.INFO,
            title=f"User Password Changed: {user_name}",
            message=f"{user_name} has changed their password.",
            action_url=f"/admin/users/{user.id}/"
        )
    
    # Send email to admins
    admin_emails = [admin.email for admin in admins if admin.email]
    
    if admin_emails:
        # Plain text version
        email_subject = f"User Password Changed: {user_name}"
        email_body_text = f"""Good day,

A user has changed their password in the PENRO WISE system.

User: {user_name} (@{user.username})
Email: {user.email}
Position: {user.position_title or 'Not specified'}

This is a routine security notification.

Access the system at: https://penrowise.onrender.com

Best regards,
PENRO WISE System
"""
        
        # HTML version
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                A user has changed their password in the PENRO WISE system.
            </p>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                👤 User Information
            </h3>
            {format_info_box("Name", user_name, "👤")}
            {format_info_box("Username", f"@{user.username}", "🔑")}
            {format_info_box("Email", user.email, "📧")}
            {format_info_box("Position", user.position_title or 'Not specified', "💼")}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    🔒 This is a routine security notification.
                </p>
            </div>
        """
        
        email_body_html = get_styled_email_html("🔒 User Password Changed", content_html)
        
        # Send to each admin individually for proper logging
        for admin in admins:
            if admin.email:
                send_logged_email(
                    recipient_email=admin.email,
                    subject=email_subject,
                    body_text=email_body_text,
                    body_html=email_body_html,
                    email_type="password_change",
                    sender=user,
                    recipient=admin,
                    fail_silently=True
                )
