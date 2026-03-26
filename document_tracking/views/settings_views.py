"""
Settings Views for Document Tracking System.

Handles document type management and configuration.
"""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db import models
import json

from document_tracking.models import DocumentType
from document_tracking.forms import DocumentTypeForm
from document_tracking.services.document_type_service import (
    get_all_document_types,
    reorder_document_types,
    can_delete_document_type,
    delete_document_type,
    get_document_type_stats,
)
from document_tracking.permissions import is_admin


@login_required
def settings_index(request):
    """
    Main settings page for Document Tracking.
    Shows overview and links to various settings sections.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    from datetime import datetime
    from document_tracking.models import Submission, TrackingNumberSequence
    
    # Get statistics
    total_document_types = DocumentType.objects.count()
    active_document_types = DocumentType.objects.filter(is_active=True).count()
    total_submissions = Submission.objects.count()
    current_year = datetime.now().year
    
    # Get this year's sequences
    this_year_sequences = TrackingNumberSequence.objects.filter(
        year=current_year
    ).select_related('document_type')
    
    context = {
        'total_document_types': total_document_types,
        'active_document_types': active_document_types,
        'total_submissions': total_submissions,
        'current_year': current_year,
        'this_year_sequences': this_year_sequences,
    }
    
    return render(request, 'document_tracking/settings/index.html', context)


@login_required
def document_types_list(request):
    """
    List all document types with management options.
    Supports drag-and-drop reordering.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    document_types = get_all_document_types()
    
    # Get statistics for each document type
    stats = {}
    for doc_type in document_types:
        stats[doc_type.id] = get_document_type_stats(doc_type.id)
    
    context = {
        'document_types': document_types,
        'stats': stats,
    }
    
    return render(request, 'document_tracking/settings/document_types.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def document_type_add(request):
    """
    Add a new document type.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    if request.method == 'POST':
        form = DocumentTypeForm(request.POST)
        if form.is_valid():
            doc_type = form.save(commit=False)
            # Set order to be last
            max_order = DocumentType.objects.aggregate(
                models.Max('order')
            )['order__max'] or 0
            doc_type.order = max_order + 1
            doc_type.save()
            
            messages.success(
                request,
                f'Document type "{doc_type.name}" created successfully!'
            )
            return redirect('document_tracking:document-types')
    else:
        form = DocumentTypeForm()
    
    context = {
        'form': form,
        'action': 'Add',
    }
    
    return render(request, 'document_tracking/settings/document_type_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def document_type_edit(request, pk):
    """
    Edit an existing document type.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    doc_type = get_object_or_404(DocumentType, pk=pk)
    
    if request.method == 'POST':
        form = DocumentTypeForm(request.POST, instance=doc_type)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Document type "{doc_type.name}" updated successfully!'
            )
            return redirect('document_tracking:document-types')
    else:
        form = DocumentTypeForm(instance=doc_type)
    
    context = {
        'form': form,
        'action': 'Edit',
        'document_type': doc_type,
    }
    
    return render(request, 'document_tracking/settings/document_type_form.html', context)


@login_required
@require_http_methods(["POST"])
def document_type_delete(request, pk):
    """
    Delete a document type (if safe to do so).
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    doc_type = get_object_or_404(DocumentType, pk=pk)
    
    # Check if can delete
    check = can_delete_document_type(pk)
    
    if not check['can_delete']:
        messages.error(request, check['reason'])
        return redirect('document_tracking:document-types')
    
    try:
        name = doc_type.name
        delete_document_type(pk)
        messages.success(
            request,
            f'Document type "{name}" deleted successfully!'
        )
    except Exception as e:
        messages.error(request, f'Error deleting document type: {str(e)}')
    
    return redirect('document_tracking:document-types')


@login_required
@require_http_methods(["POST"])
def document_types_reorder(request):
    """
    Reorder document types via AJAX.
    Expects JSON: {"type_ids": [3, 1, 2, ...]}
    """
    if not is_admin(request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'Admin access required'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        type_ids = data.get('type_ids', [])
        
        if not type_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No type IDs provided'
            }, status=400)
        
        # Reorder
        reorder_document_types(type_ids)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Document types reordered successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)



# ============================================================
# SECTION/DEPARTMENT MANAGEMENT VIEWS
# ============================================================

@login_required
def sections_list(request):
    """
    List all sections - Section Directory Management.
    Sections are used by File Manager for organizing folders.
    """
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    from document_tracking.services.section_service import get_all_sections, get_section_stats
    from document_tracking.models import Section
    
    sections = get_all_sections()
    
    # Add stats to each section
    sections_with_stats = []
    for section in sections:
        stats = get_section_stats(section.id)
        sections_with_stats.append({
            'section': section,
            'stats': stats,
        })
    
    context = {
        'sections': sections_with_stats,
        'page_title': 'Section Directory',
    }
    
    return render(request, 'document_tracking/settings/sections.html', context)


@login_required
def section_create(request):
    """Create new section."""
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    from document_tracking.forms import SectionForm
    from document_tracking.models import Section
    
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save()
            messages.success(request, f'✓ Section "{section.display_name}" created successfully')
            return redirect('document_tracking:settings_sections')
    else:
        form = SectionForm()
    
    context = {
        'form': form,
        'page_title': 'Create Section',
        'action': 'Create',
    }
    
    return render(request, 'document_tracking/settings/section_form.html', context)


@login_required
def section_edit(request, section_id):
    """Edit existing section."""
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    from document_tracking.forms import SectionForm
    from document_tracking.models import Section
    
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            section = form.save()
            messages.success(request, f'✓ Section "{section.display_name}" updated successfully')
            return redirect('document_tracking:settings_sections')
    else:
        form = SectionForm(instance=section)
    
    context = {
        'form': form,
        'section': section,
        'page_title': f'Edit Section: {section.display_name}',
        'action': 'Update',
    }
    
    return render(request, 'document_tracking/settings/section_form.html', context)


@login_required
def section_delete(request, section_id):
    """Delete section."""
    if not is_admin(request.user):
        messages.error(request, 'Admin access required.')
        return redirect('document_tracking:admin_overview')
    
    from document_tracking.services.section_service import can_delete_section, delete_section, get_section_stats
    from document_tracking.models import Section
    
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        try:
            if can_delete_section(section_id):
                section_name = section.display_name
                delete_section(section_id)
                messages.success(request, f'✓ Section "{section_name}" deleted successfully')
            else:
                messages.error(request, f'❌ Cannot delete section "{section.display_name}" - it has assigned submissions')
        except Exception as e:
            messages.error(request, f'❌ Error deleting section: {str(e)}')
        
        return redirect('document_tracking:settings_sections')
    
    # Check if can delete
    can_delete = can_delete_section(section_id)
    stats = get_section_stats(section_id)
    
    context = {
        'section': section,
        'can_delete': can_delete,
        'stats': stats,
        'page_title': f'Delete Section: {section.display_name}',
    }
    
    return render(request, 'document_tracking/settings/section_delete.html', context)
