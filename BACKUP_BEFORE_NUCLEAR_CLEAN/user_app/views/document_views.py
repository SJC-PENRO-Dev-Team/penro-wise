"""
User Documents Views - View-only access to documents dashboard and file manager.
Users can browse and download files but cannot create, edit, move, or delete.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.db.models import Count
from datetime import timedelta
import os
import re

from accounts.models import WorkItemAttachment, WorkCycle
from structure.models import DocumentFolder
from structure.services.folder_resolution import resolve_folder_context, acronym


def workcycle_acronym(title: str) -> str:
    """Acronymizes a WorkCycle title while preserving full years."""
    if not title:
        return "—"
    parts = []
    for word in title.split():
        if re.fullmatch(r"\d{4}", word):
            parts.append(word)
        else:
            parts.append(acronym(word))
    return " ".join(parts)


def file_exists(attachment):
    """Check if the actual file exists in storage."""
    if not attachment.file:
        return False
    try:
        return attachment.file.storage.exists(attachment.file.name)
    except Exception:
        return False


def get_file_size(attachment):
    """Get file size in human-readable format."""
    if not attachment.file:
        return "—"
    try:
        size = attachment.file.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return "—"


@login_required
def user_documents_dashboard(request):
    """
    User Documents Dashboard - View-only analytics and navigation.
    Shows only accepted files and user's own upload statistics.
    """
    user = request.user
    current_year = now().year
    current_month = now().month
    today = now().date()
    
    # Base queryset - only accepted files
    all_attachments = WorkItemAttachment.objects.filter(acceptance_status='accepted')
    
    # User's own uploads
    user_uploads = WorkItemAttachment.objects.filter(uploaded_by=user)
    
    # Core metrics (all accepted files)
    total_files = all_attachments.count()
    files_this_year = all_attachments.filter(uploaded_at__year=current_year).count()
    files_this_month = all_attachments.filter(
        uploaded_at__year=current_year,
        uploaded_at__month=current_month
    ).count()
    
    # User's upload stats
    user_total_uploads = user_uploads.count()
    user_accepted = user_uploads.filter(acceptance_status='accepted').count()
    user_pending = user_uploads.filter(acceptance_status='pending').count()
    user_rejected = user_uploads.filter(acceptance_status='rejected').count()
    
    # Files by type (accepted only)
    files_by_type = list(
        all_attachments
        .values('attachment_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    type_display_map = dict(WorkItemAttachment.ATTACHMENT_TYPE_CHOICES)
    for item in files_by_type:
        item['display_name'] = type_display_map.get(item['attachment_type'], item['attachment_type'])
    
    # Recent accepted files (last 10)
    recent_files = list(
        all_attachments
        .select_related('uploaded_by', 'work_item__workcycle')
        .order_by('-uploaded_at')[:10]
    )
    
    # Files by workcycle (top 5)
    files_by_workcycle = list(
        all_attachments
        .filter(work_item__workcycle__is_active=True)
        .values('work_item__workcycle__id', 'work_item__workcycle__title')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    return render(
        request,
        "user/page/documents_dashboard.html",
        {
            # Core metrics
            "total_files": total_files,
            "files_this_year": files_this_year,
            "files_this_month": files_this_month,
            
            # User stats
            "user_total_uploads": user_total_uploads,
            "user_accepted": user_accepted,
            "user_pending": user_pending,
            "user_rejected": user_rejected,
            
            # Analytics
            "files_by_type": files_by_type,
            "files_by_workcycle": files_by_workcycle,
            "recent_files": recent_files,
            
            "now": now(),
        }
    )


@login_required
def user_file_manager(request, folder_id=None):
    """
    User File Manager - View-only browsing of accepted files.
    Users can browse folders and download files but cannot modify anything.
    """
    # Clear toast message from session after displaying
    request.session.pop('toast_message', None)
    request.session.pop('toast_type', None)
    
    if folder_id:
        current_folder = get_object_or_404(DocumentFolder, id=folder_id)
    else:
        current_folder = get_object_or_404(
            DocumentFolder,
            folder_type=DocumentFolder.FolderType.ROOT,
            parent__isnull=True
        )

    breadcrumb = current_folder.get_path()
    folders = current_folder.children.all()
    
    # Get all folders for sidebar navigation with hierarchy level
    all_folders = []
    def add_folders_recursive(parent, level=0):
        children = DocumentFolder.objects.filter(parent=parent).order_by('name')
        for child in children:
            child.level = level
            all_folders.append(child)
            add_folders_recursive(child, level + 1)
    
    root_folder = DocumentFolder.objects.filter(
        folder_type=DocumentFolder.FolderType.ROOT,
        parent__isnull=True
    ).first()
    if root_folder:
        add_folders_recursive(root_folder, 1)
    
    # Only show accepted files
    attachments = current_folder.files.filter(
        acceptance_status="accepted"
    ).select_related(
        "work_item",
        "uploaded_by"
    )

    return render(
        request,
        "user/page/file_manager.html",
        {
            "current_folder": current_folder,
            "breadcrumb": breadcrumb,
            "folders": folders,
            "attachments": attachments,
            "all_folders": all_folders,
        }
    )


@login_required
def user_download_file(request, attachment_id):
    """
    Download a file - Users can only download accepted files.
    """
    attachment = get_object_or_404(
        WorkItemAttachment, 
        id=attachment_id,
        acceptance_status='accepted'
    )
    
    if not attachment.file:
        raise Http404("File not found.")
    
    try:
        response = FileResponse(
            attachment.file.open('rb'),
            as_attachment=True,
            filename=os.path.basename(attachment.file.name)
        )
        return response
    except Exception:
        raise Http404("File not found.")


@login_required
def user_all_accepted_files(request):
    """
    User view: list all accepted files (view-only, download only).
    """
    # Base queryset - only accepted files
    qs = (
        WorkItemAttachment.objects
        .filter(acceptance_status="accepted")
        .select_related(
            "uploaded_by",
            "work_item",
            "work_item__workcycle",
            "folder",
            "folder__workcycle",
        )
        .order_by("-uploaded_at")
    )

    # Filter params
    year = request.GET.get("year")
    attachment_type = request.GET.get("type")
    division = request.GET.get("division")
    search = request.GET.get("q", "")
    sort = request.GET.get("sort", "date_desc")

    # Safe DB filters
    if year:
        qs = qs.filter(work_item__workcycle__due_at__year=year)
    if attachment_type:
        qs = qs.filter(attachment_type=attachment_type)

    # Sorting
    if sort == "date_asc":
        qs = qs.order_by("uploaded_at")
    elif sort == "name_asc":
        qs = qs.order_by("file")
    elif sort == "name_desc":
        qs = qs.order_by("-file")
    else:
        qs = qs.order_by("-uploaded_at")

    filters_active = {
        "year": year,
        "type": attachment_type,
        "division": division,
        "search": search,
    }

    # Build files list
    files = []
    for attachment in qs:
        if not file_exists(attachment):
            continue

        ctx = resolve_folder_context(attachment.folder)
        workcycle = ctx["workcycle"] or getattr(attachment.work_item, "workcycle", None)

        # Division filter
        if division and ctx["division"] != division:
            continue

        file_name = attachment.file.name.rsplit("/", 1)[-1]
        
        # Search filter
        if search:
            searchable = f"{file_name} {ctx.get('division', '')}".lower()
            if search.lower() not in searchable:
                continue

        files.append({
            "id": attachment.id,
            "name": file_name,
            "file_url": attachment.file.url,
            "type": attachment.get_attachment_type_display(),
            "type_code": attachment.attachment_type,
            "workcycle": workcycle_acronym(workcycle.title) if workcycle else "—",
            "division": acronym(ctx["division"]) if ctx["division"] else "—",
            "uploaded_by": attachment.uploaded_by,
            "uploaded_at": attachment.uploaded_at,
            "file_size": get_file_size(attachment),
        })

    # Filter options
    filters = {
        "years": list(
            WorkCycle.objects
            .values_list("due_at__year", flat=True)
            .distinct()
            .order_by("-due_at__year")
        ),
        "attachment_types": WorkItemAttachment.ATTACHMENT_TYPE_CHOICES,
        "divisions": list(
            Team.objects
            .filter(team_type=Team.TeamType.DIVISION)
            .values_list("name", flat=True)
            .order_by("name")
        ),
    }

    context = {
        "files": files,
        "total_files": len(files),
        "filters": filters,
        "active": {
            "year": year,
            "type": attachment_type,
            "division": division,
            "search": search,
            "sort": sort,
        },
    }

    # Handle AJAX requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "user/page/partials/_all_files_table.html",
            context,
            request=request,
        )
        return JsonResponse({
            "html": html,
            "count": len(files),
        })

    return render(request, "user/page/all_accepted_files.html", context)



@login_required
def file_manager_create_folder(request):
    """
    Create a new folder in the current directory.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('user_app:file-manager')
    
    folder_name = request.POST.get('folder_name', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not folder_name:
        messages.error(request, 'Folder name is required')
        return redirect('user_app:file-manager-folder', folder_id=parent_id) if parent_id else redirect('user_app:file-manager')
    
    try:
        # Get parent folder - handle root folder case
        if parent_id:
            parent_folder = get_object_or_404(DocumentFolder, id=parent_id)
        else:
            # Get root folder
            parent_folder = DocumentFolder.objects.filter(
                folder_type=DocumentFolder.FolderType.ROOT,
                parent__isnull=True
            ).first()
        
        # Check if folder with same name already exists
        if DocumentFolder.objects.filter(parent=parent_folder, name=folder_name).exists():
            messages.error(request, 'A folder with this name already exists')
            return redirect('user_app:file-manager-folder', folder_id=parent_id) if parent_id else redirect('user_app:file-manager')
        
        # Create the folder
        new_folder = DocumentFolder.objects.create(
            name=folder_name,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            parent=parent_folder,
            created_by=request.user,
            is_system_generated=False
        )
        
        messages.success(request, f'Folder "{new_folder.name}" created successfully')
        
        # Redirect back to the same folder
        if parent_id:
            return redirect('user_app:file-manager-folder', folder_id=parent_id)
        else:
            return redirect('user_app:file-manager')
        
    except Exception as e:
        messages.error(request, f'Failed to create folder: {str(e)}')
        return redirect('user_app:file-manager-folder', folder_id=parent_id) if parent_id else redirect('user_app:file-manager')


@login_required
def file_manager_upload(request):
    """
    Upload files to the current directory.
    Files uploaded by admin will have admin metadata.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('user_app:file-manager')
    
    folder_id = request.POST.get('folder_id')
    files = request.FILES.getlist('files')
    
    logger.info(f"Upload attempt - folder_id: {folder_id}, files count: {len(files)}")
    
    if not files:
        messages.error(request, 'No files selected')
        return redirect('user_app:file-manager-folder', folder_id=folder_id) if folder_id else redirect('user_app:file-manager')
    
    try:
        # Get the folder - handle root folder case
        if folder_id:
            folder = get_object_or_404(DocumentFolder, id=folder_id)
            logger.info(f"Using folder: {folder.name} (ID: {folder.id})")
        else:
            # Get root folder
            folder = DocumentFolder.objects.filter(
                folder_type=DocumentFolder.FolderType.ROOT,
                parent__isnull=True
            ).first()
            logger.info(f"Using root folder: {folder.name if folder else 'None'}")
        
        if not folder:
            messages.error(request, 'Folder not found')
            return redirect('user_app:file-manager')
        
        uploaded_count = 0
        errors = []
        
        for file in files:
            try:
                logger.info(f"Uploading file: {file.name}")
                # User uploads: Set reviewed_at/reviewed_by for timestamp tracking
                # Admin uploads via file manager: Leave NULL (no review needed)
                attachment = WorkItemAttachment.objects.create(
                    file=file,
                    uploaded_by=request.user,
                    folder=folder,
                    acceptance_status='accepted',  # Auto-accept uploads
                    attachment_type='document',
                    reviewed_by=request.user if not request.user.is_staff else None,
                    reviewed_at=now() if not request.user.is_staff else None,
                )
                uploaded_count += 1
                logger.info(f"File uploaded successfully: {attachment.id}")
            except Exception as file_error:
                logger.error(f"Error uploading file {file.name}: {str(file_error)}")
                errors.append(f"{file.name}: {str(file_error)}")
        
        if uploaded_count > 0:
            uploader_name = request.user.get_full_name() or request.user.username
            # Store message in session for toast display
            request.session['toast_message'] = f'{uploaded_count} file(s) uploaded successfully'
            request.session['toast_type'] = 'success'
        
        if errors:
            request.session['toast_message'] = f'Some files failed: {", ".join(errors)}'
            request.session['toast_type'] = 'error'
        
        # Redirect back to the same folder
        if folder_id:
            return redirect('user_app:file-manager-folder', folder_id=folder_id)
        else:
            return redirect('user_app:file-manager')
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        messages.error(request, f'Upload failed: {str(e)}')
        return redirect('user_app:file-manager-folder', folder_id=folder_id) if folder_id else redirect('user_app:file-manager')


@login_required
def file_manager_delete(request):
    """
    Delete selected files and folders.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({'success': False, 'message': 'No items selected'}, status=400)
        
        deleted_folders = 0
        deleted_files = 0
        
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            
            if item_type == 'folder':
                folder = DocumentFolder.objects.filter(id=item_id, is_system_generated=False).first()
                if folder:
                    folder.delete()
                    deleted_folders += 1
            elif item_type == 'file':
                attachment = WorkItemAttachment.objects.filter(id=item_id).first()
                if attachment:
                    attachment.delete()
                    deleted_files += 1
        
        message = f'Deleted {deleted_folders} folder(s) and {deleted_files} file(s)'
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
