# file_manager_views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder


@login_required
def file_manager_view(request, folder_id=None):
    """
    Shared File Manager view for both admin and regular users.
    Admins have full access, users have read-only access.
    """
    # Determine if user is admin
    is_readonly = not request.user.is_staff
    url_namespace = 'user_app' if is_readonly else 'admin_app'
    base_template = 'user/layout/base.html' if is_readonly else 'admin/layout/base.html'
    
    # Get toast messages from session (will be cleared after rendering)
    toast_message = request.session.get('toast_message')
    toast_type = request.session.get('toast_type')
    
    if folder_id:
        current_folder = get_object_or_404(DocumentFolder, id=folder_id)
    else:
        # Get the main ROOT folder (not Document Tracking)
        # Prefer ROOT named "ROOT" over other roots
        current_folder = DocumentFolder.objects.filter(
            folder_type=DocumentFolder.FolderType.ROOT,
            parent__isnull=True,
            name="ROOT"
        ).first()
        
        if not current_folder:
            # Fallback to any ROOT folder
            current_folder = DocumentFolder.objects.filter(
                folder_type=DocumentFolder.FolderType.ROOT,
                parent__isnull=True
            ).first()
        
        if not current_folder:
            # Auto-create ROOT folder if missing
            current_folder = DocumentFolder.objects.create(
                name="ROOT",
                folder_type=DocumentFolder.FolderType.ROOT,
                parent=None,
                is_system_generated=True,
            )

    breadcrumb = current_folder.get_path()
    folders = current_folder.children.all()
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"File Manager - Folder: {current_folder.name} (ID: {current_folder.id})")
    logger.info(f"  Children count: {folders.count()}")
    for child in folders:
        logger.info(f"    - {child.name} ({child.folder_type})")
    
    # Get files and links in this folder ONLY
    # Links are now folder-specific, not global
    attachments = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        folder=current_folder
    ).select_related(
        "work_item",
        "uploaded_by"
    )
    
    # Group links by link_title
    from collections import defaultdict
    grouped_links = defaultdict(list)
    files = []
    
    for attachment in attachments:
        if attachment.is_link() and attachment.link_title:
            # Group links by their title
            grouped_links[attachment.link_title].append(attachment)
        else:
            # Regular files and links without titles
            files.append(attachment)
    
    # Convert grouped_links to a list of dicts for template
    link_groups = []
    for group_name, links in grouped_links.items():
        # Always create a group, even for single links
        # This ensures the modal is shown for all titled links
        link_groups.append({
            'name': group_name,
            'count': len(links),
            'links': links,
            'first_link': links[0],  # For metadata like upload date
        })
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"File Manager View - Folder: {current_folder.name} (ID: {current_folder.id})")
    logger.info(f"  Total attachments: {attachments.count()}")
    logger.info(f"  Grouped links: {len(link_groups)}")
    logger.info(f"  Individual files: {len(files)}")
    logger.info(f"  Subfolders: {folders.count()}")
    
    # Clear toast messages from session after getting them
    request.session.pop('toast_message', None)
    request.session.pop('toast_type', None)

    # Get all folders for sidebar tree
    all_folders = DocumentFolder.objects.all().select_related('parent')

    return render(
        request,
        "admin/page/file_manager.html",
        {
            "current_folder": current_folder,
            "breadcrumb": breadcrumb,
            "folders": folders,
            "attachments": files,  # Individual files and single links
            "link_groups": link_groups,  # Grouped links
            "all_folders": all_folders,
            "toast_message": toast_message,
            "toast_type": toast_type,
            "is_readonly": is_readonly,
            "url_namespace": url_namespace,
            "base_template": base_template,
        }
    )


@staff_member_required
def create_folder(request):
    """
    Creates a user folder under the selected parent.
    Validation is handled by the model.
    """
    if request.method != "POST":
        return redirect("admin_app:file-manager")

    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name", "").strip()

    if not name or not parent_id:
        request.session['toast_message'] = "Folder name and parent required"
        request.session['toast_type'] = 'error'
        return redirect("admin_app:file-manager")

    parent = get_object_or_404(DocumentFolder, id=parent_id)

    try:
        folder = DocumentFolder(
            name=name,
            parent=parent,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            created_by=request.user,
            is_system_generated=False,
        )
        folder.save()
        request.session['toast_message'] = f"Created folder '{name}'"
        request.session['toast_type'] = 'success'
    except ValidationError as e:
        error_msg = e.messages[0] if e.messages else "Invalid folder"
        request.session['toast_message'] = f"Failed to create folder: {error_msg}"
        request.session['toast_type'] = 'error'

    return redirect("admin_app:file-manager-folder", folder_id=parent.id)


@staff_member_required
@require_POST
def move_attachment(request):
    """
    Moves file attachments, links, and link-groups to a target folder.
    Links can now be assigned to folders.
    Returns specific error messages for invalid drops.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if this is a link-group move
    move_type = request.POST.get("type")
    group_name = request.POST.get("group_name")
    
    if move_type == "link-group" and group_name:
        # Moving a link group - get all links with this title
        folder_id = request.POST.get("folder_id")
        target_folder = get_object_or_404(DocumentFolder, id=folder_id)
        
        # Get current folder from the first link in the group
        first_link = WorkItemAttachment.objects.filter(
            link_title=group_name,
            link_url__isnull=False
        ).first()
        
        if not first_link:
            return JsonResponse(
                {"status": "error", "message": "Link group not found."},
                status=400
            )
        
        current_folder = first_link.folder
        
        # Get all links in this group from the current folder
        group_links = WorkItemAttachment.objects.filter(
            link_title=group_name,
            folder=current_folder,
            link_url__isnull=False
        )
        
        logger.info(f"Moving link group '{group_name}' with {group_links.count()} links to folder {folder_id}")
        
        moved_count = 0
        for link in group_links:
            link.folder = target_folder
            link.save()
            moved_count += 1
        
        return JsonResponse({
            "status": "success",
            "message": f"Moved link group '{group_name}' ({moved_count} links) successfully"
        })
    
    # Regular attachment move (files and individual links)
    attachment_ids = request.POST.getlist("attachment_ids[]")
    folder_id = request.POST.get("folder_id")
    
    logger.info(f"Move request - attachment_ids: {attachment_ids}, folder_id: {folder_id}")

    if not attachment_ids:
        return JsonResponse(
            {"status": "error", "message": "No files selected."},
            status=400
        )

    target_folder = get_object_or_404(DocumentFolder, id=folder_id)

    moved = []
    errors = []
    
    try:
        for attachment_id in attachment_ids:
            attachment = get_object_or_404(
                WorkItemAttachment,
                id=attachment_id
            )

            old_folder_id = attachment.folder_id
            attachment.folder = target_folder
            
            # This triggers clean() which validates the placement
            try:
                attachment.save()
                moved.append({
                    "id": attachment.id,
                    "old_folder": old_folder_id
                })
            except ValidationError as e:
                error_msg = e.messages[0] if e.messages else "Invalid drop location."
                errors.append(f"{attachment.get_filename()}: {error_msg}")
                logger.error(f"ValidationError moving attachment {attachment_id}: {error_msg}")

        # Build response message
        messages = []
        if moved:
            messages.append(f"Moved {len(moved)} item(s) successfully")
        if errors:
            messages.append(f"{len(errors)} failed: {errors[0]}")
        
        message = ". ".join(messages)
        status = "success" if moved else "error"

        return JsonResponse({
            "status": status,
            "message": message,
            "moved": moved,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Exception in move_attachment: {str(e)}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
            status=500
        )


@staff_member_required
@require_POST
def move_folder(request):
    """
    Moves folders with proper validation:
    - User-created folders: Can be moved freely (respecting hierarchy)
    - System folders: Can be moved but with warnings and validation
    - Prevents circular references and invalid hierarchy
    """
    import logging
    logger = logging.getLogger(__name__)
    
    folder_id = request.POST.get("folder_id")
    target_folder_id = request.POST.get("target_folder_id")
    force_move = request.POST.get("force_move") == "true"

    if not folder_id or not target_folder_id:
        return JsonResponse(
            {"status": "error", "message": "Missing folder IDs."},
            status=400
        )

    folder = get_object_or_404(DocumentFolder, id=folder_id)
    target_folder = get_object_or_404(DocumentFolder, id=target_folder_id)

    # Prevent moving ROOT folder
    if folder.folder_type == DocumentFolder.FolderType.ROOT:
        return JsonResponse(
            {"status": "error", "message": "ROOT folder cannot be moved."},
            status=400
        )

    # System folders require confirmation
    if folder.is_system_generated and not force_move:
        return JsonResponse({
            "status": "confirm_required",
            "message": "Moving system folders may affect work items and organizational structure",
            "folder_name": folder.name,
            "folder_type": folder.get_folder_type_display(),
            "target_name": target_folder.name,
            "has_workcycle": bool(folder.workcycle_id)
        })

    try:
        old_parent_id = folder.parent_id
        old_parent_name = folder.parent.name if folder.parent else "None"
        
        folder.parent = target_folder
        folder.save()  # This triggers validation

        logger.info(f"Moved folder '{folder.name}' from '{old_parent_name}' to '{target_folder.name}'")

        return JsonResponse({
            "status": "success",
            "message": f"Folder '{folder.name}' moved successfully.",
            "folder_id": folder.id,
            "old_parent": old_parent_id
        })

    except ValidationError as e:
        error_msg = e.messages[0] if e.messages else "Invalid folder placement."
        logger.error(f"ValidationError moving folder {folder_id}: {error_msg}")
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )
    except Exception as e:
        logger.error(f"Exception moving folder {folder_id}: {str(e)}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
            status=500
        )


@staff_member_required
@require_POST
def bulk_move(request):
    """
    Moves multiple items (files, links, folders) to a target folder.
    Handles mixed selections and provides detailed feedback.
    Links can now be moved to folders.
    """
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        target_folder_id = data.get('target_folder_id')
        
        if not items or not target_folder_id:
            return JsonResponse(
                {"status": "error", "message": "Missing items or target folder"},
                status=400
            )
        
        target_folder = get_object_or_404(DocumentFolder, id=target_folder_id)
        
        results = {
            "moved_files": [],
            "moved_links": [],
            "moved_folders": [],
            "errors": []
        }
        
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            
            try:
                if item_type == 'file':
                    attachment = get_object_or_404(WorkItemAttachment, id=item_id)
                    attachment.folder = target_folder
                    attachment.save()
                    results['moved_files'].append(attachment.get_filename())
                
                elif item_type == 'link':
                    # Links can now be moved to folders
                    attachment = get_object_or_404(WorkItemAttachment, id=item_id)
                    attachment.folder = target_folder
                    attachment.save()
                    results['moved_links'].append(attachment.get_filename())
                
                elif item_type == 'link-group':
                    # Move all links in the group
                    group_name = item.get('group_name')
                    if not group_name:
                        results['errors'].append(f"link-group {item_id}: Missing group name")
                        continue
                    
                    # Get the first link to determine the current folder
                    first_link = get_object_or_404(WorkItemAttachment, id=item_id)
                    current_folder = first_link.folder
                    
                    # Find all links with this title in the current folder
                    group_links = WorkItemAttachment.objects.filter(
                        link_title=group_name,
                        folder=current_folder,
                        link_url__isnull=False
                    )
                    
                    moved_count = 0
                    for link in group_links:
                        link.folder = target_folder
                        link.save()
                        moved_count += 1
                    
                    results['moved_links'].append(f"{group_name} ({moved_count} links)")
                
                elif item_type == 'folder':
                    folder = get_object_or_404(DocumentFolder, id=item_id)
                    
                    # Prevent moving ROOT
                    if folder.folder_type == DocumentFolder.FolderType.ROOT:
                        results['errors'].append(f"{folder.name}: ROOT cannot be moved")
                        continue
                    
                    folder.parent = target_folder
                    folder.save()
                    results['moved_folders'].append(folder.name)
            
            except ValidationError as e:
                error_msg = e.messages[0] if e.messages else "Invalid operation"
                results['errors'].append(f"{item_type} {item_id}: {error_msg}")
            except Exception as e:
                results['errors'].append(f"{item_type} {item_id}: {str(e)}")
        
        # Build summary message
        messages = []
        if results['moved_files']:
            messages.append(f"Moved {len(results['moved_files'])} file(s)")
        if results['moved_links']:
            messages.append(f"Moved {len(results['moved_links'])} link(s)")
        if results['moved_folders']:
            messages.append(f"Moved {len(results['moved_folders'])} folder(s)")
        if results['errors']:
            messages.append(f"{len(results['errors'])} failed")
        
        status = "success" if (results['moved_files'] or results['moved_links'] or results['moved_folders']) else "error"
        
        return JsonResponse({
            "status": status,
            "message": ". ".join(messages),
            "results": results
        })
    
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON data"},
            status=400
        )
    except Exception as e:
        logger.error(f"Bulk move error: {str(e)}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": f"An error occurred: {str(e)}"},
            status=500
        )


@staff_member_required
@require_POST
def bulk_delete(request):
    """
    Deletes multiple items with strict 3-step confirmation flow:
    Step 1: General confirmation (always)
    Step 2: System folder confirmation (if any system folders)
    Step 3: Non-empty folder confirmation (if any non-empty folders)
    """
    import json
    import logging
    from django.db import transaction
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        step = data.get('step', '1')
        confirmations = data.get('confirmations', {})
        
        logger.info(f"Bulk delete request - Step: {step}, Items: {items}, Confirmations: {confirmations}")
        
        if not items:
            return JsonResponse(
                {"status": "error", "message": "No items selected"},
                status=400
            )
        
        # Analyze items
        has_system_folders = False
        has_non_empty_folders = False
        folder_details = []
        file_count = 0
        link_count = 0
        link_group_count = 0
        
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            
            if item_type == 'folder':
                folder = get_object_or_404(DocumentFolder, id=item_id)
                children_count = folder.children.count()
                files_count = folder.files.count()
                is_empty = (children_count == 0 and files_count == 0)
                
                folder_details.append({
                    'id': folder.id,
                    'name': folder.name,
                    'is_system': folder.is_system_generated,
                    'is_empty': is_empty,
                    'children_count': children_count,
                    'files_count': files_count
                })
                
                if folder.is_system_generated:
                    has_system_folders = True
                if not is_empty:
                    has_non_empty_folders = True
            
            elif item_type == 'file':
                file_count += 1
            
            elif item_type == 'link':
                link_count += 1
            
            elif item_type == 'link-group':
                link_group_count += 1
        
        # Step 1: General confirmation
        if step == '1':
            return JsonResponse({
                "status": "confirm_step_1",
                "message": "Confirm bulk deletion",
                "item_count": len(items),
                "file_count": file_count,
                "link_count": link_count,
                "link_group_count": link_group_count,
                "folder_count": len(folder_details),
                "has_system_folders": has_system_folders,
                "has_non_empty_folders": has_non_empty_folders
            })
        
        # Step 2: System folder confirmation
        if step == '2' and has_system_folders:
            system_folders = [f for f in folder_details if f['is_system']]
            
            # Check if keywords provided
            keywords_provided = confirmations.get('system_folder_keywords', {})
            
            if not keywords_provided:
                # Generate keywords for all system folders
                keywords = {}
                for folder in system_folders:
                    keywords[str(folder['id'])] = folder['name'][:30].upper().replace(" ", "_")
                
                return JsonResponse({
                    "status": "confirm_step_2",
                    "message": "System folders require keyword confirmation",
                    "system_folders": system_folders,
                    "required_keywords": keywords
                })
            
            # Verify all keywords
            for folder in system_folders:
                folder_id = str(folder['id'])
                expected = folder['name'][:30].upper().replace(" ", "_")
                provided = keywords_provided.get(folder_id, "")
                
                if provided != expected:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Incorrect keyword for folder '{folder['name']}'"
                    }, status=400)
        
        # Step 3: Non-empty folder confirmation
        if step == '3' and has_non_empty_folders:
            confirmed = confirmations.get('non_empty_confirmed') == True
            
            if not confirmed:
                non_empty_folders = [f for f in folder_details if not f['is_empty']]
                
                # Calculate total impact
                total_descendants = 0
                total_files = 0
                for folder_info in non_empty_folders:
                    folder = DocumentFolder.objects.get(id=folder_info['id'])
                    to_process = [folder]
                    while to_process:
                        current = to_process.pop(0)
                        children = list(current.children.all())
                        total_descendants += len(children)
                        for child in children:
                            total_files += child.files.count()
                        to_process.extend(children)
                    total_files += folder_info['files_count']
                
                return JsonResponse({
                    "status": "confirm_step_3",
                    "message": "Some folders are not empty - confirm cascading deletion",
                    "non_empty_folders": non_empty_folders,
                    "total_descendants": total_descendants,
                    "total_files": total_files
                })
        
        # All confirmations passed - perform deletion
        try:
            with transaction.atomic():
                deleted_count = 0
                errors = []
                
                for item in items:
                    item_type = item.get('type')
                    item_id = item.get('id')
                    
                    try:
                        if item_type == 'folder':
                            folder = get_object_or_404(DocumentFolder, id=item_id)
                            
                            # Get all descendants (children, grandchildren, etc.)
                            descendants = []
                            to_process = [folder]
                            while to_process:
                                current = to_process.pop(0)
                                descendants.append(current)
                                to_process.extend(current.children.all())
                            
                            # Reverse order to delete children before parents
                            descendants.reverse()
                            
                            # Orphan attachments for system folders
                            if folder.is_system_generated:
                                for desc_folder in descendants:
                                    attachments = WorkItemAttachment.objects.filter(folder=desc_folder)
                                    for att in attachments:
                                        att.folder = None
                                        att.save()
                            
                            # Delete all descendants (including the folder itself)
                            for desc_folder in descendants:
                                desc_folder.delete()
                                deleted_count += 1
                        
                        elif item_type == 'file' or item_type == 'link':
                            attachment = get_object_or_404(WorkItemAttachment, id=item_id)
                            
                            # Check deletion permissions
                            if attachment.attachment_type == 'admin_upload':
                                pass  # Can delete
                            elif attachment.is_link():
                                pass  # Links can be deleted
                            else:
                                errors.append(f"{attachment.get_filename()}: Work item files cannot be deleted")
                                continue
                            
                            if attachment.file:
                                attachment.file.delete(save=False)
                            attachment.delete()
                            deleted_count += 1
                        
                        elif item_type == 'link-group':
                            # Delete all links in the group
                            group_name = item.get('group_name')
                            if not group_name:
                                errors.append(f"link-group {item_id}: Missing group name")
                                continue
                            
                            # Get the first link to determine the current folder
                            first_link = get_object_or_404(WorkItemAttachment, id=item_id)
                            current_folder = first_link.folder
                            
                            # Find all links with this title in the current folder
                            group_links = WorkItemAttachment.objects.filter(
                                link_title=group_name,
                                folder=current_folder,
                                link_url__isnull=False
                            )
                            
                            # Delete all links in the group
                            links_deleted = 0
                            for link in group_links:
                                # Check deletion permissions
                                if link.attachment_type == 'admin_upload' or link.is_link():
                                    link.delete()
                                    links_deleted += 1
                                else:
                                    errors.append(f"{link.get_filename()}: Work item files cannot be deleted")
                            
                            if links_deleted > 0:
                                deleted_count += links_deleted
                                logger.info(f"Deleted link group '{group_name}': {links_deleted} links")
                    
                    except Exception as e:
                        errors.append(f"{item_type} {item_id}: {str(e)}")
                
                logger.info(f"Bulk delete completed: {deleted_count} items deleted, {len(errors)} errors")
                
                if deleted_count > 0:
                    message = f"Deleted {deleted_count} item(s)"
                    if errors:
                        message += f", {len(errors)} failed"
                    
                    return JsonResponse({
                        "status": "success",
                        "message": message,
                        "deleted_count": deleted_count,
                        "errors": errors
                    })
                else:
                    error_details = {
                        "items_received": len(items),
                        "errors": errors,
                        "deleted_count": deleted_count
                    }
                    logger.error(f"No items deleted - Details: {error_details}")
                    return JsonResponse({
                        "status": "error",
                        "message": f"No items were deleted. Errors: {', '.join(errors) if errors else 'Unknown'}",
                        "errors": errors,
                        "details": error_details
                    }, status=400)
        
        except Exception as e:
            logger.error(f"Bulk delete error: {str(e)}", exc_info=True)
            return JsonResponse({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON data"},
            status=400
        )
    except Exception as e:
        logger.error(f"Bulk delete error: {str(e)}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": f"An error occurred: {str(e)}"},
            status=500
        )

# file_manager_views.py - ADD THESE NEW VIEWS

from django.http import FileResponse, Http404
import os

@staff_member_required
@require_POST
def rename_folder(request):
    """
    Renames a user-created folder.
    System folders cannot be renamed.
    """
    folder_id = request.POST.get("folder_id")
    new_name = request.POST.get("new_name", "").strip()
    
    if not folder_id or not new_name:
        request.session['toast_message'] = "Folder ID and new name required"
        request.session['toast_type'] = 'error'
        return JsonResponse(
            {"status": "error", "message": "Invalid input."},
            status=400
        )
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    if folder.is_system_generated:
        request.session['toast_message'] = "System folders cannot be renamed"
        request.session['toast_type'] = 'error'
        return JsonResponse(
            {"status": "error", "message": "System folders cannot be renamed."},
            status=400
        )
    
    try:
        old_name = folder.name
        folder.name = new_name
        folder.save()
        
        request.session['toast_message'] = f"Renamed '{old_name}' to '{new_name}'"
        request.session['toast_type'] = 'success'
        
        return JsonResponse({
            "status": "success",
            "message": f"Renamed '{old_name}' to '{new_name}'."
        })
    except ValidationError as e:
        error_msg = e.messages[0] if e.messages else "Invalid folder name."
        request.session['toast_message'] = f"Failed to rename: {error_msg}"
        request.session['toast_type'] = 'error'
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )


@staff_member_required
@require_POST
def rename_attachment(request):
    """
    Renames a file or link attachment.
    For files: renames the display name (link_title field)
    For links: renames the link title
    """
    import os
    
    attachment_id = request.POST.get("attachment_id")
    new_name = request.POST.get("new_name", "").strip()
    
    if not attachment_id or not new_name:
        return JsonResponse(
            {"status": "error", "message": "Attachment ID and new name required"},
            status=400
        )
    
    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    
    try:
        old_name = attachment.get_filename()
        
        if attachment.is_link():
            # For links, update the link_title
            attachment.link_title = new_name
            attachment.save()
        else:
            # For files, we can't rename the actual file, but we can set link_title as display name
            # Store the new name in link_title field (repurposed as display name)
            attachment.link_title = new_name
            attachment.save()
        
        request.session['toast_message'] = f"Renamed '{old_name}' to '{new_name}'"
        request.session['toast_type'] = 'success'
        
        return JsonResponse({
            "status": "success",
            "message": f"Renamed '{old_name}' to '{new_name}'"
        })
    except Exception as e:
        error_msg = str(e)
        request.session['toast_message'] = f"Failed to rename: {error_msg}"
        request.session['toast_type'] = 'error'
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )
        request.session['toast_type'] = 'error'
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )


@staff_member_required
@require_POST
def delete_folder(request):
    """
    Deletes folders with cascading deletion and strict confirmation flow:
    Step 1: General confirmation (always)
    Step 2: System folder confirmation (if applicable) - ONLY for individual delete
    Step 3: Non-empty folder confirmation (if applicable)
    
    Allows deletion of non-empty folders with proper warnings.
    For bulk delete, system folders skip step 2 (keyword) but still go through step 3.
    """
    import json
    import logging
    from django.db import transaction
    
    logger = logging.getLogger(__name__)
    
    folder_id = request.POST.get("folder_id")
    step = request.POST.get("step", "1")  # Track confirmation step
    is_bulk = request.POST.get("is_bulk", "false") == "true"  # Check if bulk delete
    
    if not folder_id:
        request.session['toast_message'] = "Folder ID required"
        request.session['toast_type'] = 'error'
        return JsonResponse({"status": "error", "message": "Folder ID required"}, status=400)
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    # Count children and files
    children_count = folder.children.count()
    files_count = folder.files.count()
    is_empty = (children_count == 0 and files_count == 0)
    
    # Step 1: General confirmation (always required)
    if step == "1":
        return JsonResponse({
            "status": "confirm_step_1",
            "message": "Confirm deletion",
            "folder_id": folder_id,
            "folder_name": folder.name,
            "folder_type": folder.get_folder_type_display(),
            "is_system": folder.is_system_generated,
            "is_empty": is_empty,
            "children_count": children_count,
            "files_count": files_count,
            "has_workcycle": bool(folder.workcycle_id)
        })
    
    # Step 2: System folder confirmation (if system-generated AND NOT bulk delete)
    if step == "2" and folder.is_system_generated and not is_bulk:
        # Generate confirmation keyword
        expected_keyword = folder.name[:30].upper().replace(" ", "_")
        confirmation_keyword = request.POST.get("confirmation_keyword", "").strip()
        
        if not confirmation_keyword:
            # First time showing step 2
            return JsonResponse({
                "status": "confirm_step_2",
                "message": "System folder requires keyword confirmation",
                "folder_id": folder_id,
                "folder_name": folder.name,
                "folder_type": folder.get_folder_type_display(),
                "confirmation_keyword": expected_keyword,
                "is_empty": is_empty,
                "children_count": children_count,
                "files_count": files_count,
                "has_workcycle": bool(folder.workcycle_id)
            })
        
        # Verify keyword
        if confirmation_keyword != expected_keyword:
            return JsonResponse({
                "status": "error",
                "message": f"Incorrect confirmation keyword. Expected: {expected_keyword}"
            }, status=400)
    
    # Step 3: Non-empty folder confirmation (if not empty)
    if step == "3" and not is_empty:
        confirmed = request.POST.get("confirmed_non_empty") == "true"
        
        if not confirmed:
            # Calculate total descendants
            total_descendants = 0
            total_files = files_count
            to_process = [folder]
            while to_process:
                current = to_process.pop(0)
                children = list(current.children.all())
                total_descendants += len(children)
                for child in children:
                    total_files += child.files.count()
                to_process.extend(children)
            
            return JsonResponse({
                "status": "confirm_step_3",
                "message": "Folder is not empty - confirm cascading deletion",
                "folder_id": folder_id,
                "folder_name": folder.name,
                "is_system": folder.is_system_generated,
                "children_count": children_count,
                "files_count": files_count,
                "total_descendants": total_descendants,
                "total_files": total_files
            })
    
    # All confirmations passed - perform deletion
    try:
        with transaction.atomic():
            folder_name = folder.name
            parent_id = folder.parent_id
            
            # Get all descendant folders for logging
            descendants = []
            to_process = [folder]
            while to_process:
                current = to_process.pop(0)
                descendants.append(current)
                to_process.extend(current.children.all())
            
            # For system folders, orphan attachments by setting folder=None
            # For user folders, CASCADE will delete them
            if folder.is_system_generated:
                for desc_folder in descendants:
                    attachments = WorkItemAttachment.objects.filter(folder=desc_folder)
                    for att in attachments:
                        # Use update() to bypass model validation
                        WorkItemAttachment.objects.filter(id=att.id).update(folder=None)
                        logger.info(f"Orphaning attachment {att.id} from deleted folder {desc_folder.name}")
            
            # Delete folders from deepest to shallowest (reverse order)
            # This avoids PROTECT foreign key errors
            for desc_folder in reversed(descendants):
                desc_folder.delete()
            
            logger.info(f"Deleted folder '{folder_name}' with {len(descendants)-1} descendants, {files_count} direct files")
            
            request.session['toast_message'] = f"Deleted folder '{folder_name}' and all contents"
            request.session['toast_type'] = 'success'
            
            return JsonResponse({
                "status": "success",
                "message": f"Deleted '{folder_name}' and all contents",
                "parent_id": parent_id
            })
    
    except Exception as e:
        logger.error(f"Error deleting folder {folder_id}: {str(e)}", exc_info=True)
        request.session['toast_message'] = f"Failed to delete folder: {str(e)}"
        request.session['toast_type'] = 'error'
        return JsonResponse({
            "status": "error",
            "message": f"Failed to delete folder: {str(e)}"
        }, status=500)


@staff_member_required
@require_POST
def delete_file(request):
    """
    Deletes a file or link attachment.
    - Admin uploads: Can always be deleted
    - Work item links: Can be deleted by owner or admin
    - Work item files: Cannot be deleted (data integrity)
    """
    attachment_id = request.POST.get("attachment_id")
    
    if not attachment_id:
        request.session['toast_message'] = "File/Link ID required"
        request.session['toast_type'] = 'error'
        return JsonResponse({"status": "error", "message": "File/Link ID required"}, status=400)
    
    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    
    # Get the name before deletion
    item_name = attachment.get_filename() or "Unknown"
    item_type = "link" if attachment.is_link() else "file"
    
    # Deletion rules:
    # 1. Admin uploads: Always deletable
    # 2. Links (any type): Deletable by owner or admin
    # 3. Work item files: NOT deletable (data integrity)
    
    if attachment.attachment_type == 'admin_upload':
        # Admin uploads can always be deleted
        pass
    elif attachment.is_link():
        # Links can be deleted by owner or admin
        if not request.user.is_staff and attachment.uploaded_by_id != request.user.id:
            request.session['toast_message'] = f"Cannot delete '{item_name}' - you can only delete your own links"
            request.session['toast_type'] = 'error'
            return JsonResponse({
                "status": "error",
                "message": "You can only delete your own links"
            }, status=403)
    else:
        # Work item files cannot be deleted
        request.session['toast_message'] = f"Cannot delete '{item_name}' - work item files cannot be deleted"
        request.session['toast_type'] = 'error'
        return JsonResponse({
            "status": "error",
            "message": "Work item files cannot be deleted (data integrity)"
        }, status=403)
    
    # Delete the actual file from storage (only for file attachments)
    if attachment.file:
        attachment.file.delete(save=False)
    
    attachment.delete()
    
    request.session['toast_message'] = f"Deleted {item_type} '{item_name}'"
    request.session['toast_type'] = 'success'
    
    return JsonResponse({
        "status": "success",
        "message": f"Deleted '{item_name}'"
    })


@login_required
def download_file(request, attachment_id):
    """
    Downloads a file attachment.
    Accessible to all logged-in users (both admin and regular users).
    """
    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    
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


@staff_member_required
def upload_files(request):
    """
    Handles multiple file uploads and link attachments to the current folder.
    Admins can upload to ANY folder including ROOT, YEAR, CATEGORY.
    """
    from django.contrib import messages
    from django.utils.timezone import now
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != "POST":
        messages.error(request, "Invalid request method")
        return redirect("admin_app:file-manager")
    
    folder_id = request.POST.get("folder_id")
    action = request.POST.get("action", "upload_files")
    
    logger.info(f"Admin upload - folder_id: {folder_id}, action: {action}")
    
    if not folder_id:
        messages.error(request, "No folder specified")
        return redirect("admin_app:file-manager")
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    # Handle file uploads
    if action == "upload_files":
        files = request.FILES.getlist("files")
        
        if not files:
            messages.error(request, "No files selected")
            return redirect("admin_app:file-manager-folder", folder_id=folder_id)
        
        logger.info(f"Admin uploading to {folder.get_folder_type_display()} folder: {folder.name}")
        
        uploaded_count = 0
        errors = []
        
        for file in files:
            try:
                logger.info(f"Uploading file: {file.name}")
                attachment = WorkItemAttachment.objects.create(
                    work_item=None,  # Standalone upload
                    file=file,
                    folder=folder,
                    uploaded_by=request.user,
                    attachment_type='admin_upload',
                    acceptance_status='accepted',
                    reviewed_by=None,
                    reviewed_at=None,
                )
                uploaded_count += 1
                logger.info(f"File uploaded: {attachment.id}")
            except Exception as e:
                logger.error(f"Error uploading {file.name}: {str(e)}")
                errors.append(f"{file.name}: {str(e)}")
                continue
        
        if uploaded_count > 0:
            request.session['toast_message'] = f"{uploaded_count} file(s) uploaded successfully"
            request.session['toast_type'] = 'success'
        
        if errors:
            request.session['toast_message'] = f"Some files failed: {', '.join(errors)}"
            request.session['toast_type'] = 'error'
    
    # Handle link attachments
    elif action == "add_links":
        # Get title
        link_title = request.POST.get("link_title", "").strip()
        
        if not link_title:
            request.session['toast_message'] = "Link title is required"
            request.session['toast_type'] = 'error'
            return redirect("admin_app:file-manager-folder", folder_id=folder_id)
        
        # Get all link inputs (link_1, link_2, etc.)
        # IMPORTANT: Skip "link_title" - only process "link_1", "link_2", etc.
        links = []
        for key in request.POST:
            if key.startswith("link_") and key != "link_title":
                link = request.POST.get(key, "").strip()
                # Additional validation: ensure it's a valid URL, not the title
                if link and link != link_title:
                    links.append(link)
        
        if not links:
            request.session['toast_message'] = "No links provided"
            request.session['toast_type'] = 'error'
            return redirect("admin_app:file-manager-folder", folder_id=folder_id)
        
        logger.info(f"Admin adding {len(links)} links with title '{link_title}' to folder: {folder.name}")
        
        added_count = 0
        errors = []
        
        for link_url in links:
            try:
                logger.info(f"Adding link: {link_url}")
                attachment = WorkItemAttachment.objects.create(
                    work_item=None,  # Standalone upload
                    link_url=link_url,
                    link_title=link_title,  # Add title
                    folder=folder,  # Assign to current folder
                    uploaded_by=request.user,
                    attachment_type='admin_upload',
                    acceptance_status='accepted',
                    reviewed_by=None,
                    reviewed_at=None,
                )
                added_count += 1
                logger.info(f"Link added: {attachment.id}")
            except Exception as e:
                logger.error(f"Error adding link {link_url}: {str(e)}")
                errors.append(f"{link_url}: {str(e)}")
                continue
        
        if added_count > 0:
            request.session['toast_message'] = f"{added_count} link(s) added successfully"
            request.session['toast_type'] = 'success'
        
        if errors:
            request.session['toast_message'] = f"Some links failed: {', '.join(errors)}"
            request.session['toast_type'] = 'error'
    
    return redirect("admin_app:file-manager-folder", folder_id=folder.id)


@staff_member_required
def get_folder_structure(request, folder_id):
    """
    Returns folder structure for navigation in move modal.
    Returns breadcrumb and child folders.
    """
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    # Get breadcrumb
    breadcrumb = []
    current = folder
    while current:
        breadcrumb.insert(0, {
            'id': current.id,
            'name': current.name,
            'is_system': current.is_system_generated
        })
        current = current.parent
    
    # Get child folders
    child_folders = folder.children.all().values(
        'id', 'name', 'is_system_generated', 'folder_type'
    )
    
    folders = []
    for child in child_folders:
        folders.append({
            'id': child['id'],
            'name': child['name'],
            'is_system': child['is_system_generated'],
            'folder_type': child['folder_type']
        })
    
    return JsonResponse({
        'status': 'success',
        'breadcrumb': breadcrumb,
        'folders': folders,
        'current_folder_path': folder.get_path_string()
    })


@login_required
def get_grouped_links(request, folder_id, group_name):
    """
    Returns all links in a group for the modal.
    Used when user clicks on a grouped link item.
    """
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    # Get all links with this group name in this folder
    # For document tracking folders (attachment type), don't filter by acceptance_status
    # since those are user submissions, not admin-reviewed files
    query = WorkItemAttachment.objects.filter(
        folder=folder,
        link_title=group_name,
        link_url__isnull=False
    )
    
    # Only filter by acceptance_status for file manager folders (not document tracking)
    if folder.folder_type != 'attachment':
        query = query.filter(acceptance_status="accepted")
    
    links = query.select_related("uploaded_by").order_by('uploaded_at')
    
    # Build response
    links_data = []
    for link in links:
        links_data.append({
            'id': link.id,
            'url': link.link_url,
            'title': link.link_title,
            'uploaded_at': link.uploaded_at.strftime('%b %d, %Y %I:%M %p'),
            'uploaded_by': link.uploaded_by.get_full_name() if link.uploaded_by else 'Unknown',
        })
    
    return JsonResponse({
        'status': 'success',
        'group_name': group_name,
        'count': len(links_data),
        'links': links_data
    })
