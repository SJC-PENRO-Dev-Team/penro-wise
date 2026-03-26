"""
Views for Digital Document Tracking System.

This module contains views for:
- User submission and viewing
- Admin tracking assignment and management
- Section officer status updates
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from document_tracking.models import Submission, Logbook, Section
from document_tracking.forms import (
    SubmissionForm, TrackingAssignmentForm, StatusChangeForm,
    ComplianceFileUploadForm, RoutingOverrideForm
)
# Import from legacy_services.py file (not services/ package)
import sys
import os
import importlib.util
_services_path = os.path.join(os.path.dirname(__file__), 'legacy_services.py')
_services_spec = importlib.util.spec_from_file_location("document_tracking._legacy_services", _services_path)
_services = importlib.util.module_from_spec(_services_spec)
_services_spec.loader.exec_module(_services)
FileService = _services.FileService
TrackingService = _services.TrackingService
StatusService = _services.StatusService
RoutingService = _services.RoutingService

from document_tracking.permissions import (
    require_view_permission, require_compliance_upload_permission,
    require_tracking_assignment_permission, require_status_change_permission,
    require_archive_permission, is_admin, get_user_sections
)
from document_tracking.email_service import DocumentTrackingEmailService
import json


# ============================================================================
# USER VIEWS (Phase 5)
# ============================================================================

@login_required
def submit_document(request):
    """
    Display submission form and handle document submission.
    Creates submission with status 'pending_tracking'.
    Supports both file uploads and link attachments.
    """
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        files = request.FILES.getlist('files')
        
        # DEBUG: Print all POST data
        print("\n=== DOCUMENT SUBMISSION DEBUG ===")
        print("POST keys:", list(request.POST.keys()))
        for key in request.POST.keys():
            if 'link' in key.lower():
                print(f"{key}: {request.POST[key]}")
        print("=================================\n")
        
        # Extract link data from POST
        link_groups = {}
        for key, value in request.POST.items():
            if key.startswith('link_group_'):
                parts = key.split('_')
                if len(parts) >= 3:
                    group_index = parts[2]
                    if group_index not in link_groups:
                        link_groups[group_index] = {'title': None, 'urls': []}
                    
                    if 'title' in key:
                        link_groups[group_index]['title'] = value
                        print(f"Found title: {value}")
                    elif 'url' in key:
                        link_groups[group_index]['urls'].append(value)
                        print(f"Found URL: {value}")
        
        print(f"\nParsed link_groups: {link_groups}")
        print(f"Number of link groups: {len(link_groups)}\n")
        
        # Validate: must have at least files or links
        has_files = len(files) > 0
        has_links = len(link_groups) > 0
        
        # Check form validity first
        if not form.is_valid():
            # Form has validation errors - show them to user
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label or field
                        messages.error(request, f'{field_label}: {error}')
        elif not (has_files or has_links):
            # No files or links attached
            messages.error(request, 'At least one file or link must be attached.')
        else:
            # Form is valid and has attachments - proceed with submission
            # Create submission
            submission = form.save(commit=False)
            submission.submitted_by = request.user
            submission.status = 'pending_tracking'
            
            # Debug: Check if doc_type was saved
            print(f"\n=== SUBMISSION SAVE DEBUG ===")
            print(f"Form cleaned_data doc_type: {form.cleaned_data.get('doc_type')}")
            print(f"Submission doc_type before save: {submission.doc_type}")
            print(f"Submission doc_type ID: {submission.doc_type.id if submission.doc_type else None}")
            print(f"=============================\n")
            
            submission.save()
            
            # Create primary folder
            primary_folder = FileService.create_primary_folder(submission)
            submission.primary_folder = primary_folder
            submission.save()
            
            # Store files if any
            if has_files:
                FileService.store_files(
                    submission=submission,
                    files=files,
                    folder=primary_folder,
                    uploaded_by=request.user
                )
            
            # Store links if any
            if has_links:
                from accounts.models import WorkItemAttachment
                
                print(f"\nStoring {len(link_groups)} link groups...")
                
                for group_data in link_groups.values():
                    title = group_data['title']
                    urls = group_data['urls']
                    
                    print(f"  Group title: {title}")
                    print(f"  URLs in group: {urls}")
                    
                    if not urls:
                        print(f"  WARNING: No URLs found for group '{title}'")
                        continue
                    
                    for url in urls:
                        url_clean = url.strip()
                        if not url_clean:
                            print(f"    Skipping empty URL")
                            continue
                        
                        # Auto-fix URL format
                        # 1. Add protocol if missing
                        if not url_clean.startswith(('http://', 'https://', 'ftp://')):
                            url_clean = 'https://' + url_clean
                            print(f"    Auto-prepended https://: {url_clean}")
                        
                        # 2. Add .com if no domain extension (e.g., "aynata" -> "aynata.com")
                        url_without_protocol = url_clean.replace('https://', '').replace('http://', '').replace('ftp://', '')
                        domain_part = url_without_protocol.split('/')[0].split('?')[0]
                        
                        if '.' not in domain_part and ':' not in domain_part:  # No TLD and not localhost:port
                            # Insert .com before any path or query
                            if '/' in url_without_protocol:
                                parts = url_without_protocol.split('/', 1)
                                url_clean = url_clean.replace(url_without_protocol, parts[0] + '.com/' + parts[1])
                            elif '?' in url_without_protocol:
                                parts = url_without_protocol.split('?', 1)
                                url_clean = url_clean.replace(url_without_protocol, parts[0] + '.com?' + parts[1])
                            else:
                                url_clean = url_clean + '.com'
                            print(f"    Auto-appended .com: {url_clean}")
                        
                        # Try to create attachment
                        try:
                            print(f"    Creating attachment for URL: {url_clean}")
                            att = WorkItemAttachment.objects.create(
                                folder=primary_folder,
                                link_url=url_clean,
                                link_title=title,
                                uploaded_by=request.user,
                                attachment_type='document',
                                acceptance_status='accepted'  # Auto-accept for document tracking
                            )
                            print(f"    ✓ Created attachment ID: {att.id}")
                        except Exception as e:
                            print(f"    ✗ ERROR: Failed to create attachment for '{url_clean}': {e}")
                            messages.warning(request, f"Could not save link '{url}': Invalid URL format. Please use a valid domain (e.g., example.com)")
                
                print("Link storage complete\n")
            
            # Create logbook entry
            attachment_info = []
            if has_files:
                attachment_info.extend([f.name for f in files])
            if has_links:
                for group_data in link_groups.values():
                    attachment_info.append(f"Links: {group_data['title']}")
            
            Logbook.objects.create(
                submission=submission,
                action='created',
                new_status='pending_tracking',
                remarks='Initial submission',
                file_names=json.dumps(attachment_info),
                actor=request.user
            )
            
            messages.success(
                request,
                f'Submission "{submission.title}" created successfully. '
                f'Tracking number will be assigned by admin.'
            )
            
            # Send acknowledgment email
            DocumentTrackingEmailService.send_submission_acknowledgment(submission)
            
            return redirect('document_tracking:my_submissions')
    else:
        form = SubmissionForm()
    
    return render(request, 'document_tracking/submit.html', {'form': form})


@login_required
def my_submissions(request):
    """
    List all submissions by current user with filtering and pagination.
    """
    submissions = Submission.objects.filter(
        submitted_by=request.user
    ).select_related('assigned_section', 'primary_folder')
    
    # Get total count before filtering
    total_count = submissions.count()
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get status choices for filter
    status_choices = Submission._meta.get_field('status').choices
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'current_status': status_filter,
        'total_count': total_count,
    }
    return render(request, 'document_tracking/my_submissions.html', context)


@login_required
@require_view_permission
def submission_detail(request, submission_id):
    """
    Display submission details, files, and logbook.
    Show compliance upload form if status allows.
    """
    submission = get_object_or_404(
        Submission.objects.select_related(
            'submitted_by', 'assigned_section', 'primary_folder', 'archive_folder', 'doc_type'
        ),
        id=submission_id
    )
    
    # Get logbook entries
    logbook_entries = submission.logs.select_related('actor').order_by('-timestamp')
    
    # Check if user can upload compliance files
    can_upload_compliance = (
        submission.submitted_by == request.user and
        submission.status in ['for_compliance', 'returned_to_sender']
    )
    
    # Group links by title for display
    link_groups = {}
    single_links = []
    file_attachments = []
    
    if submission.primary_folder:
        from collections import defaultdict
        temp_groups = defaultdict(list)
        
        for att in submission.primary_folder.files.all():
            if att.link_url:
                # It's a link
                if att.link_title:
                    temp_groups[att.link_title].append(att)
                else:
                    single_links.append(att)
            else:
                # It's a file
                file_attachments.append(att)
        
        # Separate grouped links (multiple with same title) from single links
        for title, links in temp_groups.items():
            if len(links) > 1:
                link_groups[title] = links
            else:
                single_links.extend(links)
    
    context = {
        'submission': submission,
        'logbook_entries': logbook_entries,
        'can_upload_compliance': can_upload_compliance,
        'link_groups': link_groups,
        'single_links': single_links,
        'file_attachments': file_attachments,
    }
    return render(request, 'document_tracking/submission_detail.html', context)


@login_required
@require_compliance_upload_permission
def upload_compliance_files(request, submission_id):
    """
    Handle additional file uploads for compliance.
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        form = ComplianceFileUploadForm(
            request.POST, request.FILES, submission=submission
        )
        files = request.FILES.getlist('files')
        
        if form.is_valid() and files:
            # Store files in primary folder
            FileService.store_files(
                submission=submission,
                files=files,
                folder=submission.primary_folder,
                uploaded_by=request.user
            )
            
            # Create logbook entry
            file_names = [f.name for f in files]
            Logbook.objects.create(
                submission=submission,
                action='files_uploaded',
                remarks=form.cleaned_data.get('remarks', ''),
                file_names=json.dumps(file_names),
                actor=request.user
            )
            
            messages.success(
                request,
                f'{len(files)} compliance file(s) uploaded successfully.'
            )
            return redirect('document_tracking:submission_detail', submission_id=submission.id)
    
    return redirect('document_tracking:submission_detail', submission_id=submission.id)


# ============================================================================
# ADMIN VIEWS (Phase 6)
# ============================================================================

@login_required
def admin_overview(request):
    """
    Admin overview with statistics and quick access.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    # Get status counts
    status_counts = {
        'pending_tracking': Submission.objects.filter(status='pending_tracking').count(),
        'received': Submission.objects.filter(status='received').count(),
        'under_review': Submission.objects.filter(status='under_review').count(),
        'for_compliance': Submission.objects.filter(status='for_compliance').count(),
        'returned_to_sender': Submission.objects.filter(status='returned_to_sender').count(),
        'approved': Submission.objects.filter(status='approved').count(),
        'rejected': Submission.objects.filter(status='rejected').count(),
    }
    
    # Status priority for sorting (pending_tracking highest, rejected last)
    status_priority = {
        'pending_tracking': 1,
        'received': 2,
        'under_review': 3,
        'for_compliance': 4,
        'returned_to_sender': 5,
        'approved': 6,
        'rejected': 7,
    }
    
    # Get recent submissions (limit 7, prioritized by status)
    all_recent = Submission.objects.select_related(
        'submitted_by', 'assigned_section'
    ).order_by('-created_at')[:20]  # Get more to ensure we have variety
    
    # Sort by priority and limit to 7
    recent_submissions = sorted(
        all_recent,
        key=lambda x: status_priority.get(x.status, 99)
    )[:7]
    
    context = {
        'status_counts': status_counts,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'document_tracking/admin_overview.html', context)




@login_required
def admin_submissions(request):
    """
    List all submissions with filters (admin only).
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    submissions = Submission.objects.select_related(
        'submitted_by', 'assigned_section'
    ).all()
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Section filter
    section_filter = request.GET.get('section')
    if section_filter:
        submissions = submissions.filter(assigned_section_id=section_filter)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        submissions = submissions.filter(
            Q(title__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(submitted_by__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get TOTAL count (unfiltered) for "All" button
    total_count = Submission.objects.count()
    
    # Get status counts for filter badges
    status_counts = {}
    for value, label in Submission._meta.get_field('status').choices:
        count = Submission.objects.filter(status=value).count()
        if count > 0:  # Only include statuses with documents
            status_counts[value] = count
    
    # Get choices with counts for template
    status_choices_with_counts = []
    for value, label in Submission._meta.get_field('status').choices:
        count = status_counts.get(value, 0)
        status_choices_with_counts.append({
            'value': value,
            'label': label,
            'count': count
        })
    
    # Get choices for filters
    status_choices = Submission._meta.get_field('status').choices
    sections = Section.objects.all()
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'status_choices_with_counts': status_choices_with_counts,
        'status_counts': status_counts,
        'total_count': total_count,
        'sections': sections,
        'current_status': status_filter,
        'current_section': section_filter,
        'search_query': search_query,
    }
    return render(request, 'document_tracking/admin_list.html', context)


@login_required
def admin_submission_detail(request, submission_id):
    """
    Display submission with admin actions (admin only).
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    # Import StatusWorkflow at the beginning
    from .workflow import StatusWorkflow
    
    submission = get_object_or_404(
        Submission.objects.select_related(
            'submitted_by', 'assigned_section', 'primary_folder', 'archive_folder', 'file_manager_folder', 'doc_type'
        ),
        id=submission_id
    )
    
    # Get files
    files = []
    if submission.primary_folder:
        files = submission.primary_folder.files.all()
    if submission.archive_folder:
        files = submission.archive_folder.files.all()
    
    # Get logbook entries with status labels
    logs = submission.logs.select_related('actor').all()
    
    # Add human-readable status labels to each log entry
    for log in logs:
        if log.old_status:
            old_info = StatusWorkflow.get_status_info(log.old_status)
            log.old_status_label = old_info.get('label', log.old_status.replace('_', ' ').title())
        else:
            log.old_status_label = None
            
        if log.new_status:
            new_info = StatusWorkflow.get_status_info(log.new_status)
            log.new_status_label = new_info.get('label', log.new_status.replace('_', ' ').title())
        else:
            log.new_status_label = None
    
    # Forms
    tracking_form = None
    if not submission.tracking_number:
        # Use new TrackingNumberAssignmentForm
        from document_tracking.forms import TrackingNumberAssignmentForm
        tracking_form = TrackingNumberAssignmentForm(submission=submission)
    
    status_form = StatusChangeForm(current_status=submission.status)
    routing_form = RoutingOverrideForm()
    
    # Get workflow information
    status_actions = StatusWorkflow.get_status_actions(submission.status)
    workflow_path = StatusWorkflow.get_workflow_path(submission)
    current_status_info = StatusWorkflow.get_status_info(submission.status)
    progress_percentage = StatusWorkflow.get_progress_percentage(submission.status)
    is_terminal = StatusWorkflow.is_terminal_status(submission.status)
    can_reset = StatusWorkflow.can_reset_to_start(submission.status)
    previous_status = StatusWorkflow.get_previous_status(submission.status, workflow_path)
    
    # Format previous status display name
    previous_status_display = None
    if previous_status:
        previous_status_display = StatusWorkflow.get_status_info(previous_status).get('label', previous_status.replace('_', ' ').title())
    
    # Get active sections for department assignment
    from document_tracking.models import Section
    from datetime import datetime
    active_sections = Section.objects.filter(is_active=True).order_by('order', 'name')
    current_year = datetime.now().year
    
    context = {
        'submission': submission,
        'files': files,
        'logbook_entries': logs,
        'tracking_form': tracking_form,
        'status_form': status_form,
        'routing_form': routing_form,
        'status_actions': status_actions,
        'workflow_path': workflow_path,
        'current_status_info': current_status_info,
        'progress_percentage': progress_percentage,
        'is_terminal': is_terminal,
        'can_reset': can_reset,
        'previous_status': previous_status,
        'previous_status_display': previous_status_display,
        'active_sections': active_sections,
        'current_year': current_year,
    }
    return render(request, 'document_tracking/admin_detail.html', context)


@login_required
@require_tracking_assignment_permission
def assign_tracking(request, submission_id):
    """
    Handle serial number assignment.
    Uses new document type system (PREFIX-YEAR-XXX format).
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check if already assigned and locked
    if submission.tracking_number and submission.tracking_locked:
        messages.error(request, 'Serial number is already assigned and locked.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        from document_tracking.forms import TrackingNumberAssignmentForm
        form = TrackingNumberAssignmentForm(request.POST, submission=submission)
        
        if form.is_valid():
            document_type = form.cleaned_data['document_type']
            assignment_mode = form.cleaned_data['assignment_mode']
            year = form.cleaned_data['year']
            manual_serial = form.cleaned_data.get('manual_serial')
            
            try:
                # Import services
                from document_tracking.services.tracking_number_service import assign_tracking_number
                
                # Assign tracking number
                tracking_number = assign_tracking_number(
                    submission=submission,
                    document_type=document_type,
                    year=year,
                    serial=manual_serial
                )
                
                # Auto-route to first active section
                from document_tracking.models import Section
                section = Section.objects.filter(is_active=True).first()
                if not section:
                    raise ValidationError("No active sections available for routing")
                
                submission.assigned_section = section
                submission.status = 'received'
                submission.save()
                
                # Create logbook entry
                Logbook.objects.create(
                    submission=submission,
                    action='tracking_assigned',
                    remarks=f"Serial number assigned: {tracking_number} (mode: {assignment_mode})",
                    actor=request.user
                )
                
                messages.success(
                    request,
                    f'✓ Serial number "{tracking_number}" assigned and locked successfully. '
                    f'Routed to {section.get_name_display()}.'
                )
                
                # Send tracking assigned email (don't let email errors affect success)
                try:
                    DocumentTrackingEmailService.send_tracking_assigned(submission)
                except Exception as email_error:
                    # Log email error but don't show to user
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Email notification failed for submission {submission.id}: {email_error}")
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a duplicate tracking number error
                if 'already exists' in error_msg.lower():
                    messages.error(
                        request, 
                        f'⚠️ Duplicate Tracking Number: {error_msg}. Please use a different serial number.'
                    )
                else:
                    messages.error(request, f'❌ Error assigning serial number: {error_msg}')
        else:
            # Form validation errors - show each error clearly
            if form.non_field_errors():
                for error in form.non_field_errors():
                    # Check if it's a duplicate error
                    if 'already exists' in str(error).lower():
                        messages.error(request, f'⚠️ Duplicate Tracking Number: {error}')
                    else:
                        messages.error(request, f'❌ {error}')
            
            for field, errors in form.errors.items():
                if field != '__all__':
                    field_label = form.fields[field].label or field.replace('_', ' ').title()
                    for error in errors:
                        messages.error(request, f'❌ {field_label}: {error}')
    
    return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)


@login_required
@require_tracking_assignment_permission
def assign_section(request, submission_id):
    """Assign section/department to submission."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        section_id = request.POST.get('section')
        
        if not section_id:
            messages.error(request, '❌ Please select a department/section')
            return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
        
        try:
            from document_tracking.models import Section
            section = Section.objects.get(id=section_id, is_active=True)
            
            # Assign section
            submission.assigned_section = section
            submission.save()
            
            # Create logbook entry
            Logbook.objects.create(
                submission=submission,
                action='section_assigned',
                remarks=f'Department assigned: {section.display_name}',
                actor=request.user
            )
            
            messages.success(
                request,
                f'✓ Department "{section.display_name}" assigned successfully. You can now approve this submission.'
            )
            
        except Section.DoesNotExist:
            messages.error(request, '❌ Invalid department/section selected')
        except Exception as e:
            messages.error(request, f'❌ Error assigning department: {str(e)}')
    
    return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)


@login_required
@require_status_change_permission
def change_status(request, submission_id):
    """
    Handle status change with validation.
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check if tracking number is assigned
    if not submission.tracking_number:
        messages.error(request, 'Please assign a tracking number before changing status.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        form = StatusChangeForm(request.POST, current_status=submission.status)
        
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            remarks = form.cleaned_data.get('remarks', '')
            
            try:
                old_status = submission.status
                StatusService.change_status(
                    submission=submission,
                    new_status=new_status,
                    actor=request.user,
                    remarks=remarks
                )
                
                messages.success(
                    request,
                    f'Status changed to "{submission.get_status_display()}" successfully.'
                )
                
                # Send status change email
                DocumentTrackingEmailService.send_status_change_notification(
                    submission=submission,
                    old_status=old_status,
                    new_status=new_status,
                    remarks=remarks
                )
                
            except Exception as e:
                messages.error(request, f'Error changing status: {str(e)}')
            
            return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)




@login_required
def reset_to_start(request, submission_id):
    """
    Reset submission back to initial state.
    Admin-only action with required remarks.
    Available from Step 2 onwards.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    if submission.status == 'pending_tracking':
        messages.error(request, 'Submission is already at initial state.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        
        try:
            StatusService.reset_to_start(
                submission=submission,
                actor=request.user,
                remarks=remarks
            )
            
            messages.success(
                request,
                f'Submission "{submission.tracking_number}" has been reset to initial state. '
                f'The submission is now unlocked and can be reprocessed.'
            )
            
            # Send email notification about reset
            DocumentTrackingEmailService.send_status_change_notification(
                submission=submission,
                old_status=submission.status,
                new_status='pending_tracking',
                remarks=f"Submission reset to start by admin. Reason: {remarks}"
            )
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error resetting submission: {str(e)}')
        
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    # Show confirmation page
    return render(request, 'document_tracking/reset_confirm.html', {'submission': submission})


@login_required
def undo_last_action(request, submission_id):
    """
    Undo the last status change.
    Admin-only action.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    if submission.status == 'pending_tracking':
        messages.error(request, 'Cannot undo from initial state.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        
        try:
            old_status = submission.status
            StatusService.undo_last_action(
                submission=submission,
                actor=request.user,
                remarks=remarks
            )
            
            messages.success(
                request,
                f'Successfully undone last action. Status reverted from '
                f'"{dict(submission._meta.get_field("status").choices).get(old_status)}" to '
                f'"{submission.get_status_display()}".'
            )
            
            # Send email notification
            DocumentTrackingEmailService.send_status_change_notification(
                submission=submission,
                old_status=old_status,
                new_status=submission.status,
                remarks=f"Action undone by admin. {remarks}" if remarks else "Action undone by admin."
            )
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error undoing action: {str(e)}')
        
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    # Show confirmation page
    from .workflow import StatusWorkflow
    workflow_path = StatusWorkflow.get_workflow_path(submission)
    previous_status = StatusWorkflow.get_previous_status(submission.status, workflow_path)
    
    context = {
        'submission': submission,
        'previous_status': previous_status,
        'previous_status_display': dict(submission._meta.get_field('status').choices).get(previous_status, previous_status) if previous_status else None,
    }
    return render(request, 'document_tracking/undo_confirm.html', context)


@login_required
def delete_submission(request, submission_id):
    """
    Permanently delete a rejected submission and all related data.
    
    SECURITY:
    - Only admin users can delete
    - Only rejected submissions can be deleted
    - Requires POST request with confirmation
    - All related data is deleted (files, links, logs)
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Import deletion service
    from document_tracking.services.deletion_service import (
        delete_rejected_submission,
        can_delete_submission
    )
    
    # Check if deletion is allowed
    check_result = can_delete_submission(submission, request.user)
    
    if not check_result['can_delete']:
        messages.error(request, check_result['reason'])
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    # Only allow POST requests (modal-based deletion)
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    confirmation = request.POST.get('confirmation', '').strip()
    
    # Require explicit confirmation
    if confirmation != 'DELETE':
        messages.error(request, 'Deletion cancelled. You must type "DELETE" to confirm.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    try:
        result = delete_rejected_submission(submission, request.user)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('document_tracking:admin_submissions')
        else:
            messages.error(request, 'Deletion failed. Please try again.')
            return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    except Exception as e:
        messages.error(request, f'Error deleting submission: {str(e)}')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)


# ============================================================================
# SECTION OFFICER VIEWS (Phase 7)
# ============================================================================

@login_required
def section_submissions(request):
    """
    List submissions assigned to officer's section.
    """
    user_sections = get_user_sections(request.user)
    
    if not user_sections.exists():
        messages.info(request, 'You are not assigned to any section.')
        return redirect('document_tracking:my_submissions')
    
    submissions = Submission.objects.filter(
        assigned_section__in=user_sections
    ).select_related('submitted_by', 'assigned_section')
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get status choices for filter
    status_choices = Submission._meta.get_field('status').choices
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'current_status': status_filter,
        'user_sections': user_sections,
    }
    return render(request, 'document_tracking/section_list.html', context)


@login_required
@require_status_change_permission
def section_update_status(request, submission_id):
    """
    Allow section officer to update status for assigned submissions.
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verify officer belongs to assigned section
    user_sections = get_user_sections(request.user)
    if submission.assigned_section not in user_sections:
        messages.error(request, 'You do not have permission to update this submission.')
        return redirect('document_tracking:section_submissions')
    
    if request.method == 'POST':
        form = StatusChangeForm(request.POST, current_status=submission.status)
        
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            remarks = form.cleaned_data.get('remarks', '')
            
            try:
                StatusService.change_status(
                    submission=submission,
                    new_status=new_status,
                    actor=request.user,
                    remarks=remarks
                )
                
                messages.success(
                    request,
                    f'Status changed to "{submission.get_status_display()}" successfully.'
                )
            except Exception as e:
                messages.error(request, f'Error changing status: {str(e)}')
            
            return redirect('document_tracking:section_submissions')
    
    # Show form
    form = StatusChangeForm(current_status=submission.status)
    context = {
        'submission': submission,
        'form': form,
    }
    return render(request, 'document_tracking/section_status_update.html', context)



@login_required
def revert_workflow(request, submission_id):
    """
    Revert workflow to a previous step.
    Admin-only action with mandatory reason.
    Allows reverting to any previously visited step.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:my_submissions')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check if submission has any history to revert to
    from document_tracking.models import Logbook
    has_history = Logbook.objects.filter(
        submission=submission,
        action='status_changed'
    ).exists()
    
    if not has_history and submission.status == 'pending_tracking':
        messages.error(request, 'No workflow history available to revert.')
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        from document_tracking.forms import WorkflowRevertForm
        form = WorkflowRevertForm(submission, request.POST)
        
        if form.is_valid():
            target_status = form.cleaned_data['target_status']
            reason = form.cleaned_data['reason']
            
            try:
                # Import workflow module
                from document_tracking.workflow import StatusWorkflow
                
                # Get status info for logging
                current_status_info = StatusWorkflow.get_status_info(submission.status)
                target_status_info = StatusWorkflow.get_status_info(target_status)
                
                current_label = current_status_info.get('label', submission.get_status_display())
                target_label = target_status_info.get('label', target_status)
                
                # Store old status for email
                old_status = submission.status
                
                # Update submission status
                submission.status = target_status
                submission.save()
                
                # Create logbook entry
                Logbook.objects.create(
                    submission=submission,
                    action='workflow_reverted',
                    old_status=old_status,
                    new_status=target_status,
                    remarks=f"Reverted from {current_label} to {target_label}. Reason: {reason}",
                    actor=request.user
                )
                
                messages.success(
                    request,
                    f'✓ Workflow reverted from "{current_label}" to "{target_label}" successfully.'
                )
                
                # Send email notification
                DocumentTrackingEmailService.send_status_change_notification(
                    submission=submission,
                    old_status=old_status,
                    new_status=target_status,
                    remarks=f"Workflow reverted by {request.user.get_full_name()}. Reason: {reason}"
                )
                
            except Exception as e:
                messages.error(request, f'Error reverting workflow: {str(e)}')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        return redirect('document_tracking:admin_submission_detail', submission_id=submission.id)
    
    # GET request - show confirmation page
    from document_tracking.forms import WorkflowRevertForm
    form = WorkflowRevertForm(submission)
    
    context = {
        'submission': submission,
        'form': form,
    }
    
    return render(request, 'document_tracking/revert_confirm.html', context)
