"""
Permission decorators and helper functions for Digital Document Tracking System.

This module contains permission checks for:
- User access control
- Admin capabilities
- Section officer permissions
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Submission, Section
import logging

logger = logging.getLogger(__name__)


# Helper Functions

def is_admin(user):
    """
    Check if user is an admin.
    Returns True if user has admin login_role.
    """
    return user.is_authenticated and getattr(user, 'login_role', None) == 'admin'


def is_section_officer(user):
    """
    Check if user is a section officer.
    Returns True if user is assigned to any section.
    """
    if not user.is_authenticated:
        return False
    return Section.objects.filter(officers=user).exists()


def get_user_sections(user):
    """
    Get all sections assigned to a user.
    Returns queryset of Section objects.
    """
    if not user.is_authenticated:
        return Section.objects.none()
    return Section.objects.filter(officers=user)


# Permission Check Functions

def user_can_view_submission(user, submission):
    """
    Check if user can view a submission.
    
    Rules:
    - User can view if they are the submitter
    - Admin can view all submissions
    - Section officer can view submissions assigned to their section
    
    Returns: bool
    """
    if not user.is_authenticated:
        return False
    
    # Admin can view all
    if is_admin(user):
        return True
    
    # User can view their own submissions
    if submission.submitted_by == user:
        return True
    
    # Section officer can view submissions in their section
    if submission.assigned_section:
        user_sections = get_user_sections(user)
        if submission.assigned_section in user_sections:
            return True
    
    return False


def user_can_upload_compliance(user, submission):
    """
    Check if user can upload compliance files.
    
    Rules:
    - User must be the submitter
    - Status must be 'for_compliance' or 'returned_to_sender'
    
    Returns: bool
    """
    if not user.is_authenticated:
        return False
    
    # Must be the submitter
    if submission.submitted_by != user:
        return False
    
    # Status must allow uploads
    allowed_statuses = ['for_compliance', 'returned_to_sender']
    return submission.status in allowed_statuses


def user_can_assign_tracking(user):
    """
    Check if user can assign tracking numbers.
    
    Rules:
    - Only admin can assign tracking numbers
    
    Returns: bool
    """
    return is_admin(user)


def user_can_change_status(user, submission):
    """
    Check if user can change submission status.
    
    Rules:
    - Admin can change any status
    - Section officer can change status for submissions in their section
    
    Returns: bool
    """
    if not user.is_authenticated:
        return False
    
    # Admin can change any status
    if is_admin(user):
        return True
    
    # Section officer can change status for their section
    if submission.assigned_section:
        user_sections = get_user_sections(user)
        if submission.assigned_section in user_sections:
            return True
    
    return False


def user_can_archive(user):
    """
    Check if user can archive submissions.
    
    Rules:
    - Only admin can archive
    
    Returns: bool
    """
    return is_admin(user)


# Decorators

def require_view_permission(view_func):
    """
    Decorator to check if user can view a submission.
    Expects submission_id in view kwargs.
    """
    @wraps(view_func)
    def wrapper(request, submission_id, *args, **kwargs):
        submission = get_object_or_404(Submission, id=submission_id)
        
        if not user_can_view_submission(request.user, submission):
            logger.warning(
                f'Permission denied: User {request.user.id} attempted to view '
                f'submission {submission_id} without permission'
            )
            return HttpResponseForbidden(
                'You do not have permission to view this submission.'
            )
        
        return view_func(request, submission_id, *args, **kwargs)
    
    return wrapper


def require_compliance_upload_permission(view_func):
    """
    Decorator to check if user can upload compliance files.
    Expects submission_id in view kwargs.
    """
    @wraps(view_func)
    def wrapper(request, submission_id, *args, **kwargs):
        submission = get_object_or_404(Submission, id=submission_id)
        
        if not user_can_upload_compliance(request.user, submission):
            logger.warning(
                f'Permission denied: User {request.user.id} attempted to upload '
                f'compliance files for submission {submission_id} without permission'
            )
            return HttpResponseForbidden(
                'You do not have permission to upload files for this submission.'
            )
        
        return view_func(request, submission_id, *args, **kwargs)
    
    return wrapper


def require_tracking_assignment_permission(view_func):
    """
    Decorator to check if user can assign tracking numbers.
    """
    @wraps(view_func)
    def wrapper(request, submission_id=None, *args, **kwargs):
        if not user_can_assign_tracking(request.user):
            logger.warning(
                f'Permission denied: User {request.user.id} attempted to assign '
                f'tracking number without admin permission'
            )
            
            # Determine return URL
            return_url = None
            if submission_id:
                return_url = f'/documents/submission/{submission_id}/'
            elif request.META.get('HTTP_REFERER'):
                return_url = request.META.get('HTTP_REFERER')
            
            # Render styled error page
            from django.shortcuts import render
            return render(request, 'document_tracking/permission_denied.html', {
                'error_message': 'You do not have permission to assign tracking numbers.',
                'return_url': return_url,
            }, status=403)
        
        return view_func(request, submission_id, *args, **kwargs) if submission_id else view_func(request, *args, **kwargs)
    
    return wrapper


def require_status_change_permission(view_func):
    """
    Decorator to check if user can change submission status.
    Expects submission_id in view kwargs.
    """
    @wraps(view_func)
    def wrapper(request, submission_id, *args, **kwargs):
        submission = get_object_or_404(Submission, id=submission_id)
        
        if not user_can_change_status(request.user, submission):
            logger.warning(
                f'Permission denied: User {request.user.id} attempted to change '
                f'status for submission {submission_id} without permission'
            )
            return HttpResponseForbidden(
                'You do not have permission to change the status of this submission.'
            )
        
        return view_func(request, submission_id, *args, **kwargs)
    
    return wrapper


def require_archive_permission(view_func):
    """
    Decorator to check if user can archive submissions.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not user_can_archive(request.user):
            logger.warning(
                f'Permission denied: User {request.user.id} attempted to archive '
                f'submission without admin permission'
            )
            return HttpResponseForbidden(
                'You do not have permission to archive submissions. Admin access required.'
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
