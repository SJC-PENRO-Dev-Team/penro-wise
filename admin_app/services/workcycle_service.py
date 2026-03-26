from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
import logging

from accounts.models import (
    WorkCycle,
    WorkAssignment,
    WorkItem,
    WorkforcesDepartment,
    WorkCycleJob,
)

from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)

User = get_user_model()
logger = logging.getLogger(__name__)


@transaction.atomic
def create_workcycle_with_assignments(
    *,
    title,
    description,
    due_at,
    created_by,
    users,
    department=None,
):
    """
    Creates a WorkCycle and WorkAssignments ONLY.
    Returns immediately without creating WorkItems or sending notifications.
    
    A WorkCycleJob is created with status=PENDING for async processing.
    """

    if not users.exists() and not department:
        raise ValueError("Must assign at least one user or a department.")

    # =====================================================
    # CREATE WORK CYCLE
    # =====================================================
    workcycle = WorkCycle.objects.create(
        title=title,
        description=description,
        due_at=due_at,
        created_by=created_by,
    )

    # =====================================================
    # CREATE WORK ASSIGNMENTS (FAST)
    # =====================================================
    assignments_to_create = []

    # Department assignment
    if department:
        assignments_to_create.append(
            WorkAssignment(
                workcycle=workcycle,
                assigned_department=department
            )
        )

    # Direct user assignments
    for user in users:
        assignments_to_create.append(
            WorkAssignment(
                workcycle=workcycle,
                assigned_user=user
            )
        )

    WorkAssignment.objects.bulk_create(assignments_to_create)

    # =====================================================
    # CREATE JOB FOR ASYNC PROCESSING
    # =====================================================
    WorkCycleJob.objects.create(
        workcycle=workcycle,
        status="pending"
    )

    return workcycle


@transaction.atomic
def process_workcycle_job(job):
    """
    Processes a WorkCycleJob by:
    1. Resolving assigned users from WorkAssignments
    2. Bulk creating WorkItems
    3. Bulk creating in-app notifications
    4. Sending emails (with error handling)
    
    This function is called by the management command.
    """

    workcycle = job.workcycle
    assigned_user_ids = set()

    # =====================================================
    # RESOLVE USERS FROM ASSIGNMENTS
    # =====================================================
    assignments = WorkAssignment.objects.filter(
        workcycle=workcycle
    ).select_related("assigned_user", "assigned_department")

    for assignment in assignments:
        # Direct user assignment
        if assignment.assigned_user:
            assigned_user_ids.add(assignment.assigned_user_id)

        # Department assignment - expand to users in that department
        if assignment.assigned_department:
            department = assignment.assigned_department
            
            # Find all users in this department
            dept_users = User.objects.filter(
                department=department,
                login_role="user"
            ).values_list("id", flat=True)

            assigned_user_ids.update(dept_users)

    if not assigned_user_ids:
        logger.warning(f"No users found for WorkCycle#{workcycle.id}")
        return
    # =====================================================
    # BULK CREATE WORK ITEMS
    # =====================================================
    existing_items = set(
        WorkItem.objects.filter(
            workcycle=workcycle
        ).values_list("owner_id", flat=True)
    )

    work_items_to_create = [
        WorkItem(workcycle=workcycle, owner_id=user_id)
        for user_id in assigned_user_ids
        if user_id not in existing_items
    ]

    if work_items_to_create:
        WorkItem.objects.bulk_create(work_items_to_create, batch_size=500)

    # =====================================================
    # BULK CREATE IN-APP NOTIFICATIONS
    # =====================================================
    users = User.objects.filter(
        id__in=assigned_user_ids,
        is_active=True,
    )

    notifications_to_create = [
        Notification(
            recipient=user,
            category=Notification.Category.ASSIGNMENT,
            priority=Notification.Priority.INFO,
            title="New work assigned",
            message=(
                f"You have been assigned to the work cycle "
                f'"{workcycle.title}".'
            ),
            workcycle=workcycle,
            action_url="/user/work-items/",
        )
        for user in users
    ]

    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create, batch_size=500)

    # =====================================================
    # SEND EMAILS (WITH ERROR HANDLING)
    # =====================================================
    email_errors = []
    
    for user in users:
        if not user.email:
            continue

        try:
            _send_assignment_email(user, workcycle, workcycle.created_by)
        except Exception as e:
            error_msg = f"Email failed for {user.email}: {str(e)}"
            logger.error(error_msg)
            email_errors.append(error_msg)

    # Log email errors but don't fail the job
    if email_errors:
        logger.warning(
            f"WorkCycle#{workcycle.id} completed with {len(email_errors)} email errors"
        )


def _send_assignment_email(user, workcycle, assigned_by):
    """
    Helper function to send assignment email to a single user.
    Separated for better error handling.
    """

    user_name = user.get_full_name() or user.username
    subject = "Notice: New Work Cycle Assignment"

    # Plain text version
    body_text = (
        f"Good day, {user_name}.\n\n"
        f"This is to inform you that you have been assigned to the work cycle "
        f'"{workcycle.title}".\n\n'
        f"Please log in to the system to review the details, requirements, "
        f"and applicable deadlines associated with this assignment.\n\n"
    )

    if assigned_by:
        body_text += f"This assignment was issued by {assigned_by}.\n\n"

    body_text += (
        f"This notice is issued for your information and appropriate action.\n\n"
        f"Access the system at: {SITE_URL}\n\n"
        f"— PENRO WISE System"
    )

    # HTML version
    assigned_by_html = ""
    if assigned_by:
        assigned_by_html = f"""
        <p style="color: #64748b; font-size: 14px; margin: 16px 0 0 0;">
            This assignment was issued by: <strong>{assigned_by}</strong>
        </p>
        """

    content_html = f"""
        <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
            Good day, <strong>{user_name}</strong>!
        </p>
        <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
            This is to inform you that you have been assigned to a new work cycle.
        </p>
        
        <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            📋 Assignment Details
        </h3>
        {format_info_box("Work Cycle", workcycle.title, "📁")}
        {format_info_box("Due Date", workcycle.due_at.strftime("%A, %d %B %Y") if workcycle.due_at else "Not specified", "📅")}
        
        {assigned_by_html}
        
        <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #0369a1; font-size: 14px;">
                💡 Please log in to the system to review the details, requirements, 
                and applicable deadlines associated with this assignment.
            </p>
        </div>
    """

    body_html = get_styled_email_html(
        "📋 New Work Cycle Assignment", 
        content_html,
        action_url="/user/work-items/",
        action_text="View My Work Items"
    )

    send_logged_email(
        recipient_email=user.email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        email_type="assignment",
        recipient=user,
        fail_silently=False  # Raise exception on error
    )
