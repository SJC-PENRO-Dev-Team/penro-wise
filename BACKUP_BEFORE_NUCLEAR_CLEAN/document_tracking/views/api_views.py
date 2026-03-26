"""
API Views for Document Tracking System.

Provides JSON endpoints for AJAX requests.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from document_tracking.services.tracking_number_service import (
    generate_tracking_number,
    validate_tracking_number,
    format_tracking_number_preview,
)
from document_tracking.services.document_type_service import get_active_document_types
from document_tracking.models import DocumentType


@login_required
@require_http_methods(["POST"])
def api_generate_tracking_number(request):
    """
    Generate a tracking number via AJAX.
    
    POST data:
    {
        "document_type_id": 1,
        "year": 2026,  // optional
        "serial": 42   // optional, for manual mode
    }
    
    Returns:
    {
        "status": "success",
        "tracking_number": "MEM-2026-001",
        "preview": "MEM-2026-001"
    }
    """
    try:
        data = json.loads(request.body)
        
        document_type_id = data.get('document_type_id')
        year = data.get('year')
        serial = data.get('serial')
        
        if not document_type_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Document type ID is required'
            }, status=400)
        
        # Get document type
        try:
            document_type = DocumentType.objects.get(id=document_type_id)
        except DocumentType.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Document type not found'
            }, status=404)
        
        # Generate tracking number
        try:
            tracking_number = generate_tracking_number(
                document_type=document_type,
                year=year,
                serial=serial
            )
            
            return JsonResponse({
                'status': 'success',
                'tracking_number': tracking_number,
                'preview': tracking_number
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
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


@login_required
@require_http_methods(["POST"])
def api_validate_tracking_number(request):
    """
    Validate a tracking number via AJAX.
    
    POST data:
    {
        "tracking_number": "MEM-2026-001",
        "exclude_submission_id": 5  // optional
    }
    
    Returns:
    {
        "status": "success",
        "valid": true,
        "errors": [],
        "parsed": {
            "prefix": "MEM",
            "year": 2026,
            "serial": 1
        }
    }
    """
    try:
        data = json.loads(request.body)
        
        tracking_number = data.get('tracking_number')
        exclude_submission_id = data.get('exclude_submission_id')
        
        if not tracking_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Tracking number is required'
            }, status=400)
        
        # Validate
        validation = validate_tracking_number(
            tracking_number=tracking_number,
            exclude_submission_id=exclude_submission_id
        )
        
        return JsonResponse({
            'status': 'success',
            'valid': validation['valid'],
            'errors': validation['errors'],
            'parsed': validation['parsed']
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


@login_required
@require_http_methods(["GET"])
def api_document_types(request):
    """
    Get active document types as JSON.
    
    Returns:
    {
        "status": "success",
        "document_types": [
            {
                "id": 1,
                "name": "Memorandum",
                "prefix": "MEM",
                "description": "...",
                "serial_mode": "auto",
                "preview": "MEM-2026-XXX"
            },
            ...
        ]
    }
    """
    try:
        from datetime import datetime
        
        document_types = get_active_document_types()
        current_year = datetime.now().year
        
        types_data = []
        for doc_type in document_types:
            types_data.append({
                'id': doc_type.id,
                'name': doc_type.name,
                'prefix': doc_type.prefix,
                'description': doc_type.description,
                'serial_mode': doc_type.serial_mode,
                'reset_annually': doc_type.reset_annually,
                'preview': format_tracking_number_preview(doc_type, current_year)
            })
        
        return JsonResponse({
            'status': 'success',
            'document_types': types_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_check_serial_availability(request):
    """
    Check if a serial number is available for a given document type and year.
    
    SECURITY: Admin-only endpoint with rate limiting via debounce on frontend.
    
    POST data:
    {
        "document_type_id": 1,
        "year": 2026,
        "serial": 42
    }
    
    Returns:
    {
        "status": "success",
        "available": true,
        "message": "Serial number is available"
    }
    OR
    {
        "status": "success",
        "available": false,
        "message": "Serial number already exists"
    }
    """
    # Security: Admin-only access
    if request.user.login_role != 'admin':
        return JsonResponse({
            'status': 'error',
            'message': 'Admin access required'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        document_type_id = data.get('document_type_id')
        year = data.get('year')
        serial = data.get('serial')
        
        # Validate required fields
        if not all([document_type_id, year, serial]):
            return JsonResponse({
                'status': 'error',
                'message': 'document_type_id, year, and serial are required'
            }, status=400)
        
        # Validate serial is a number
        try:
            serial = int(serial)
            if serial < 1 or serial > 999999999999:  # 12-digit max
                return JsonResponse({
                    'status': 'error',
                    'message': 'Serial must be between 1 and 999,999,999,999'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'Serial must be a valid number'
            }, status=400)
        
        # Get document type
        try:
            document_type = DocumentType.objects.get(id=document_type_id)
        except DocumentType.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Document type not found'
            }, status=404)
        
        # Check availability using existing tracking number service
        from document_tracking.models import TrackingNumberSequence
        
        # Check if this serial already exists for this document type and year
        # The sequence tracks last_serial, so check if requested serial <= last_serial
        sequence = TrackingNumberSequence.objects.filter(
            document_type=document_type,
            year=year
        ).first()
        
        if sequence and serial <= sequence.last_serial:
            # Serial has already been used
            exists = True
        else:
            # Serial is available (either no sequence exists or serial > last_serial)
            exists = False
        
        if exists:
            return JsonResponse({
                'status': 'success',
                'available': False,
                'message': 'Serial number already exists'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'available': True,
                'message': 'Serial number is available'
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
