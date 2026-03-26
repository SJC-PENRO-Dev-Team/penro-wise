"""
Services package for Document Tracking System.

This package contains business logic services:
- tracking_number_service: Tracking number generation and validation
- document_type_service: Document type management

Legacy services (FileService, TrackingService, StatusService, etc.) are in document_tracking/legacy_services.py
"""
from .tracking_number_service import (
    generate_tracking_number,
    validate_tracking_number,
    parse_tracking_number,
    get_next_serial,
    is_tracking_number_unique,
    format_tracking_number_preview,
)

from .document_type_service import (
    get_all_document_types,
    get_active_document_types,
    reorder_document_types,
    can_delete_document_type,
    delete_document_type,
    get_document_type_stats,
)

__all__ = [
    # Tracking number service
    'generate_tracking_number',
    'validate_tracking_number',
    'parse_tracking_number',
    'get_next_serial',
    'is_tracking_number_unique',
    'format_tracking_number_preview',
    
    # Document type service
    'get_all_document_types',
    'get_active_document_types',
    'reorder_document_types',
    'can_delete_document_type',
    'delete_document_type',
    'get_document_type_stats',
]
