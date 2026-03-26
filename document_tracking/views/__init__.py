"""
Views package for Document Tracking System.

This package organizes views into separate modules:
- settings_views: Document type management and settings
- api_views: API endpoints for AJAX requests
- Main views remain in parent views.py for backward compatibility
"""
# Import from settings and API views
from .settings_views import (
    settings_index,
    document_types_list,
    document_type_add,
    document_type_edit,
    document_type_delete,
    document_types_reorder,
)

from .api_views import (
    api_generate_tracking_number,
    api_validate_tracking_number,
    api_document_types,
    api_check_serial_availability,
)

__all__ = [
    # Settings views
    'settings_index',
    'document_types_list',
    'document_type_add',
    'document_type_edit',
    'document_type_delete',
    'document_types_reorder',
    
    # API views
    'api_generate_tracking_number',
    'api_validate_tracking_number',
    'api_document_types',
    'api_check_serial_availability',
]
