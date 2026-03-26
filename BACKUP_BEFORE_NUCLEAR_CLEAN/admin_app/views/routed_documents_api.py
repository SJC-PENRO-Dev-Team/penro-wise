"""
API views for Routed Documents filtering
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string

from document_tracking.models import Submission, DocumentType, Section


@login_required
def search_submissions(request):
    """
    Search submissions by title (real-time autocomplete)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    submissions = Submission.objects.filter(
        title__icontains=query
    ).select_related('doc_type', 'assigned_section').values(
        'id', 'title', 'tracking_number', 'status', 
        'doc_type__name', 'assigned_section__name'
    ).distinct()[:10]
    
    results = [
        {
            'id': sub['id'],
            'title': sub['title'],
            'tracking_number': sub['tracking_number'] or 'Not assigned',
            'status': dict(Submission.STATUS_CHOICES).get(sub['status'], sub['status']),
            'doc_type': sub['doc_type__name'] or 'No type',
            'section': sub['assigned_section__name'] or 'No section'
        }
        for sub in submissions
    ]
    
    return JsonResponse({'results': results})


@login_required
def search_tracking_numbers(request):
    """
    Search by tracking number (real-time autocomplete)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    submissions = Submission.objects.filter(
        tracking_number__icontains=query
    ).exclude(
        tracking_number__isnull=True
    ).exclude(
        tracking_number=''
    ).select_related('doc_type', 'assigned_section').values(
        'id', 'title', 'tracking_number', 'status',
        'doc_type__name', 'assigned_section__name'
    ).distinct()[:10]
    
    results = [
        {
            'id': sub['id'],
            'title': sub['title'],
            'tracking_number': sub['tracking_number'],
            'status': dict(Submission.STATUS_CHOICES).get(sub['status'], sub['status']),
            'doc_type': sub['doc_type__name'] or 'No type',
            'section': sub['assigned_section__name'] or 'No section'
        }
        for sub in submissions
    ]
    
    return JsonResponse({'results': results})


@login_required
def search_tracking_numbers_filter(request):
    """
    Search tracking numbers for filtering dropdown
    Returns tracking numbers with submission info, grouped by document type
    """
    query = request.GET.get('q', '').strip()
    
    results = []
    
    if query:
        # Search tracking numbers that contain the query
        submissions = Submission.objects.filter(
            tracking_number__icontains=query
        ).exclude(
            tracking_number__isnull=True
        ).exclude(
            tracking_number=''
        ).select_related('doc_type', 'assigned_section').order_by('tracking_number')[:15]
        
        for submission in submissions:
            results.append({
                'id': submission.tracking_number,
                'title': submission.tracking_number,
                'tracking_number': submission.title[:50] + ('...' if len(submission.title) > 50 else ''),
                'doc_type': submission.doc_type.name if submission.doc_type else 'No type',
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status),
                'section': submission.assigned_section.name if submission.assigned_section else 'No section'
            })
    else:
        # When no query, return all tracking numbers grouped by document type
        from collections import defaultdict
        doc_type_groups = defaultdict(list)
        
        submissions = Submission.objects.filter(
            tracking_number__isnull=False
        ).exclude(
            tracking_number=''
        ).select_related('doc_type', 'assigned_section').order_by('doc_type__name', 'tracking_number')
        
        for submission in submissions:
            doc_type_name = submission.doc_type.name if submission.doc_type else 'No Type'
            doc_type_groups[doc_type_name].append({
                'id': submission.tracking_number,
                'title': submission.tracking_number,
                'tracking_number': submission.title[:50] + ('...' if len(submission.title) > 50 else ''),
                'doc_type': doc_type_name,
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status),
                'section': submission.assigned_section.name if submission.assigned_section else 'No section'
            })
        
        # Flatten results with document type headers
        for doc_type, tracking_numbers in doc_type_groups.items():
            # Add document type header
            results.append({
                'id': f'header_{doc_type}',
                'title': f'📁 {doc_type}',
                'tracking_number': f'{len(tracking_numbers)} documents',
                'is_header': True,
                'doc_type': doc_type
            })
            
            # Add tracking numbers for this document type (limit to 5 per type)
            results.extend(tracking_numbers[:5])
            
            if len(tracking_numbers) > 5:
                results.append({
                    'id': f'more_{doc_type}',
                    'title': f'... and {len(tracking_numbers) - 5} more',
                    'tracking_number': 'Type to search for specific tracking numbers',
                    'is_more': True,
                    'doc_type': doc_type
                })
    
    return JsonResponse({'results': results[:25]})


@login_required
def search_document_types(request):
    """
    Search document types for filtering
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        # Return all active document types
        doc_types = DocumentType.objects.filter(is_active=True)
    else:
        doc_types = DocumentType.objects.filter(
            Q(name__icontains=query) | Q(prefix__icontains=query),
            is_active=True
        )
    
    results = []
    for dt in doc_types[:10]:
        submission_count = Submission.objects.filter(doc_type=dt).count()
        results.append({
            'id': dt.id,
            'title': dt.name,
            'tracking_number': f"{dt.prefix} ({submission_count} submissions)",
            'prefix': dt.prefix,
            'submission_count': submission_count
        })
    
    return JsonResponse({'results': results})


@login_required
def search_document_status(request):
    """
    Search document status for filtering
    Returns all statuses with counts when no query provided (for dropdown)
    """
    query = request.GET.get('q', '').strip().lower()
    
    results = []
    for status_code, status_display in Submission.STATUS_CHOICES:
        # If query provided, filter by status display name
        if query and query not in status_display.lower():
            continue
            
        submission_count = Submission.objects.filter(status=status_code).count()
        
        # Only include statuses that have submissions (unless query is provided)
        if submission_count > 0 or query:
            results.append({
                'id': status_code,
                'title': status_display,
                'tracking_number': f"{submission_count} submissions",
                'submission_count': submission_count
            })
    
    # Sort by submission count (descending) for better UX
    results.sort(key=lambda x: x['submission_count'], reverse=True)
    
    return JsonResponse({'results': results[:10]})


@login_required
def search_sections(request):
    """
    Search sections for filtering
    Returns all sections with counts when no query provided (for dropdown)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        sections = Section.objects.filter(is_active=True)
    else:
        sections = Section.objects.filter(
            Q(name__icontains=query) | Q(display_name__icontains=query),
            is_active=True
        )
    
    results = []
    for section in sections[:10]:
        submission_count = Submission.objects.filter(assigned_section=section).count()
        
        # Include all sections when no query, only sections with submissions when searching
        if submission_count > 0 or not query:
            results.append({
                'id': section.id,
                'title': section.display_name or section.name,
                'tracking_number': f"{submission_count} submissions",
                'submission_count': submission_count
            })
    
    # Sort by submission count (descending) for better UX
    results.sort(key=lambda x: x['submission_count'], reverse=True)
    
    return JsonResponse({'results': results})


@login_required
def search_file_names(request):
    """
    Search by file/asset name (real-time autocomplete)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in submission attachments
    from accounts.models import WorkItemAttachment
    
    # Search files
    file_attachments = WorkItemAttachment.objects.filter(
        Q(file__icontains=query) | Q(link_title__icontains=query),
        folder__folder_type='attachment'  # Document tracking attachments
    ).select_related('folder').distinct()[:10]
    
    results = []
    seen_submissions = set()
    
    for attachment in file_attachments:
        if attachment.folder:
            # Find submission through folder relationships
            submission = None
            folder = attachment.folder
            
            # Check different submission relationships
            if hasattr(folder, 'primary_submissions') and folder.primary_submissions.exists():
                submission = folder.primary_submissions.first()
            elif hasattr(folder, 'archived_submissions') and folder.archived_submissions.exists():
                submission = folder.archived_submissions.first()
            elif hasattr(folder, 'tracked_submissions') and folder.tracked_submissions.exists():
                submission = folder.tracked_submissions.first()
            
            if submission and submission.id not in seen_submissions:
                seen_submissions.add(submission.id)
                
                # Get file name
                if attachment.is_link():
                    file_name = attachment.link_title or 'Link'
                else:
                    file_name = attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown'
                
                results.append({
                    'id': submission.id,
                    'title': submission.title,
                    'tracking_number': submission.tracking_number or 'Not assigned',
                    'file_name': file_name,
                    'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status),
                    'doc_type': submission.doc_type.name if submission.doc_type else 'No type',
                    'section': submission.assigned_section.name if submission.assigned_section else 'No section'
                })
    
    return JsonResponse({'results': results})


@login_required
def get_routed_documents_by_filter(request):
    """
    Get routed documents filtered by various criteria
    """
    filter_type = request.GET.get('filter_type')  # 'doc_type', 'status', 'section', 'submission', 'tracking', 'file'
    filter_value = request.GET.get('filter_value')  # filter value
    
    if not filter_type or not filter_value:
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
    
    try:
        # Build query based on filter type
        if filter_type == 'doc_type':
            doc_type_id = int(filter_value)
            submissions = Submission.objects.filter(doc_type_id=doc_type_id)
            filter_info = DocumentType.objects.get(id=doc_type_id)
            filter_display = f"Document Type: {filter_info.name}"
            
        elif filter_type == 'status':
            submissions = Submission.objects.filter(status=filter_value)
            filter_display = f"Status: {dict(Submission.STATUS_CHOICES).get(filter_value, filter_value)}"
            
        elif filter_type == 'section':
            section_id = int(filter_value)
            submissions = Submission.objects.filter(assigned_section_id=section_id)
            filter_info = Section.objects.get(id=section_id)
            filter_display = f"Section: {filter_info.display_name or filter_info.name}"
            
        elif filter_type == 'tracking':
            # Filter by tracking number
            submissions = Submission.objects.filter(tracking_number=filter_value)
            if not submissions.exists():
                return JsonResponse({'status': 'error', 'message': 'Tracking number not found'}, status=404)
            submission = submissions.first()
            filter_display = f"Tracking Number: {filter_value}"
            
        elif filter_type in ['submission', 'file']:
            # Single submission filters (existing functionality)
            submission_id = int(filter_value)
            submissions = Submission.objects.filter(id=submission_id)
            if not submissions.exists():
                return JsonResponse({'status': 'error', 'message': 'Submission not found'}, status=404)
            filter_display = f"Submission: {submissions.first().title}"
            
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid filter type'}, status=400)
            
    except (ValueError, DocumentType.DoesNotExist, Section.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Invalid filter value'}, status=404)
    
    # Check if we have any submissions
    if not submissions.exists():
        # Return empty result with proper message
        context = {
            'files': [],
            'total_files': 0,
            'filter_display': filter_display,
            'filter_type': filter_type,
            'submissions_count': 0,
            'is_readonly': False,
            'empty_message': f'No submissions found for {filter_display.lower()}'
        }
        
        html = render_to_string('admin/page/partials/_routed_documents_content.html', context, request=request)
        
        return JsonResponse({
            'status': 'success',
            'html': html,
            'filter_display': filter_display,
            'total_files': 0,
            'submissions_count': 0
        })
    
    # Get all attachments for these submissions
    from accounts.models import WorkItemAttachment
    from collections import defaultdict
    
    # Find all folders related to these submissions
    folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            folder_ids.append(submission.file_manager_folder_id)
    
    # Also find folders that reference these submissions
    from structure.models import DocumentFolder
    related_folders = DocumentFolder.objects.filter(
        Q(primary_submissions__in=submissions) |
        Q(archived_submissions__in=submissions) |
        Q(tracked_submissions__in=submissions)
    ).distinct()
    
    folder_ids.extend([f.id for f in related_folders])
    
    # Remove duplicates and None values
    folder_ids = list(set(filter(None, folder_ids)))
    
    if not folder_ids:
        # No folders found for these submissions
        context = {
            'files': [],
            'total_files': 0,
            'filter_display': filter_display,
            'filter_type': filter_type,
            'submissions_count': submissions.count(),
            'is_readonly': False,
            'empty_message': f'No files found for {filter_display.lower()}'
        }
        
        html = render_to_string('admin/page/partials/_routed_documents_content.html', context, request=request)
        
        return JsonResponse({
            'status': 'success',
            'html': html,
            'filter_display': filter_display,
            'total_files': 0,
            'submissions_count': submissions.count()
        })
    
    # Get attachments from these folders
    attachments = WorkItemAttachment.objects.filter(
        folder_id__in=folder_ids,
        folder__folder_type='attachment'
    ).select_related('uploaded_by', 'folder').order_by('-uploaded_at')
    
    # Group links by title and build files list
    grouped_links = defaultdict(list)
    regular_items = []
    
    for attachment in attachments:
        if attachment.is_link() and attachment.link_title:
            grouped_links[attachment.link_title].append(attachment)
        else:
            regular_items.append(attachment)
    
    # Build files list with submission metadata
    files = []
    
    # Add grouped links
    for group_name, links in grouped_links.items():
        first_link = links[0]
        # Find associated submission
        submission = find_submission_for_attachment(first_link, submissions)
        
        files.append({
            'id': first_link.id,
            'name': group_name,
            'is_link_group': True,
            'link_count': len(links),
            'links': [{'url': link.link_url, 'id': link.id} for link in links],
            'uploaded_at': first_link.uploaded_at,
            'uploaded_by': first_link.uploaded_by,
            'submission': submission,
            'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
            'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
            'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
            'tracking_number': submission.tracking_number if submission else 'Not assigned'
        })
    
    # Add regular items
    for attachment in regular_items:
        submission = find_submission_for_attachment(attachment, submissions)
        
        if attachment.is_link():
            files.append({
                'id': attachment.id,
                'name': attachment.link_title or 'Link',
                'file_url': attachment.link_url,
                'is_link': True,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'submission': submission,
                'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
                'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
                'tracking_number': submission.tracking_number if submission else 'Not assigned'
            })
        else:
            files.append({
                'id': attachment.id,
                'name': attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown',
                'file_url': attachment.file.url if attachment.file else '',
                'is_link': False,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'submission': submission,
                'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
                'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
                'tracking_number': submission.tracking_number if submission else 'Not assigned'
            })
    
    # Render HTML
    context = {
        'files': files,
        'total_files': len(files),
        'filter_display': filter_display,
        'filter_type': filter_type,
        'submissions_count': submissions.count(),
        'is_readonly': False,
    }
    
    html = render_to_string('admin/page/partials/_routed_documents_content.html', context, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html,
        'filter_display': filter_display,
        'total_files': len(files),
        'submissions_count': submissions.count()
    })


def find_submission_for_attachment(attachment, submissions_queryset):
    """Helper function to find the submission associated with an attachment"""
    if not attachment.folder:
        return None
    
    folder = attachment.folder
    
    # Check different submission relationships
    for submission in submissions_queryset:
        if (submission.primary_folder_id == folder.id or
            submission.archive_folder_id == folder.id or
            submission.file_manager_folder_id == folder.id):
            return submission
    
    # Check reverse relationships
    if hasattr(folder, 'primary_submissions'):
        for submission in folder.primary_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
            return submission
    
    if hasattr(folder, 'archived_submissions'):
        for submission in folder.archived_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
            return submission
    
    if hasattr(folder, 'tracked_submissions'):
        for submission in folder.tracked_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
            return submission
    
    return None


# Legacy function for backward compatibility
@login_required
def get_routed_documents(request):
    """
    Legacy function - redirects to new filtering system
    """
    return get_routed_documents_by_filter(request)
