"""
Download as ZIP functionality for file manager
"""
import os
import zipfile
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder
import logging

logger = logging.getLogger(__name__)


@login_required
@require_POST
def download_selected_as_zip(request):
    """
    Download selected files and folders as a ZIP file.
    Preserves structure relative to selected items (not from ROOT).
    """
    import json
    
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return HttpResponse("No items selected", status=400)
        
        logger.info(f"Creating ZIP for {len(items)} items")
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            files_added = 0
            added_paths = set()
            
            for item in items:
                item_type = item.get('type')
                item_id = item.get('id')
                
                logger.info(f"Processing {item_type} with ID {item_id}")
                
                if item_type == 'file':
                    # Add single file - just the filename, no folder path
                    try:
                        attachment = WorkItemAttachment.objects.get(id=item_id)
                        if attachment.file:
                            file_name = os.path.basename(attachment.file.name)
                            
                            # Avoid duplicates by adding folder name if needed
                            zip_path = file_name
                            counter = 1
                            while zip_path in added_paths:
                                name, ext = os.path.splitext(file_name)
                                zip_path = f"{name}_{counter}{ext}"
                                counter += 1
                            
                            # Read and add file to ZIP
                            file_path = attachment.file.path
                            with open(file_path, 'rb') as f:
                                zip_file.writestr(zip_path, f.read())
                            
                            added_paths.add(zip_path)
                            files_added += 1
                            logger.info(f"Added file to ZIP: {zip_path}")
                    except Exception as e:
                        logger.error(f"Error adding file {item_id}: {e}")
                        continue
                
                elif item_type == 'folder':
                    # Add folder with its name as root in ZIP
                    try:
                        folder = DocumentFolder.objects.get(id=item_id)
                        
                        # Use folder name as base path in ZIP
                        count = add_folder_to_zip(zip_file, folder, folder.name, added_paths)
                        files_added += count
                        logger.info(f"Added folder '{folder.name}' with {count} files")
                    except Exception as e:
                        logger.error(f"Error adding folder {item_id}: {e}")
                        continue
            
            logger.info(f"Total files added to ZIP: {files_added}")
        
        # Prepare response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="download.zip"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating ZIP: {e}", exc_info=True)
        return HttpResponse(f"Error creating ZIP: {str(e)}", status=500)


def add_folder_to_zip(zip_file, folder, base_path="", added_paths=None):
    """
    Recursively add folder contents to ZIP file.
    Returns the number of files added.
    
    Args:
        zip_file: ZipFile object to write to
        folder: DocumentFolder object to process
        base_path: Current path in the ZIP (e.g., "Alright")
        added_paths: Set of paths already added (to avoid duplicates)
    """
    if added_paths is None:
        added_paths = set()
    
    files_added = 0
    
    logger.info(f"Processing folder: {folder.name}, base_path: {base_path}")
    
    # Create the folder entry in ZIP (folders end with /)
    folder_entry = base_path + '/'
    if folder_entry not in added_paths:
        zip_file.writestr(folder_entry, '')
        added_paths.add(folder_entry)
        logger.info(f"Created folder entry in ZIP: {folder_entry}")
    
    # Add all accepted files in this folder
    files_in_folder = folder.files.filter(acceptance_status="accepted")
    logger.info(f"Found {files_in_folder.count()} accepted files in folder {folder.name}")
    
    for attachment in files_in_folder:
        if attachment.file:
            try:
                # Get the actual file path
                file_path = attachment.file.path
                
                # Check if file exists
                if not os.path.exists(file_path):
                    logger.warning(f"File does not exist: {file_path}")
                    continue
                
                file_name = os.path.basename(attachment.file.name)
                zip_path = base_path + '/' + file_name
                
                # Avoid duplicates
                if zip_path not in added_paths:
                    # Read and add file to ZIP
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        zip_file.writestr(zip_path, file_content)
                    
                    added_paths.add(zip_path)
                    files_added += 1
                    logger.info(f"Added file to ZIP: {zip_path} ({len(file_content)} bytes)")
                else:
                    logger.warning(f"Skipping duplicate: {zip_path}")
            except Exception as e:
                logger.error(f"Error adding file {attachment.id} to ZIP: {e}", exc_info=True)
                continue
    
    # Recursively add subfolders
    subfolders = folder.children.all()
    logger.info(f"Found {subfolders.count()} subfolders in {folder.name}")
    
    for subfolder in subfolders:
        subfolder_path = base_path + '/' + subfolder.name
        logger.info(f"Processing subfolder: {subfolder.name}")
        
        # Add subfolder contents recursively
        count = add_folder_to_zip(zip_file, subfolder, subfolder_path, added_paths)
        files_added += count
    
    logger.info(f"Total files added from folder {folder.name}: {files_added}")
    return files_added

