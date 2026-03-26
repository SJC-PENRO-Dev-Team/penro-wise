# Document Tracking Settings - Requirements

## Overview
Implement a settings page for Document Tracking that allows admins to configure custom document types and tracking number formats.

## Features

### 1. Document Types Management
- Admin can add, edit, and delete document types
- Each document type has:
  - Name (e.g., "Memorandum", "Letter", "Report")
  - Custom prefix for tracking numbers (e.g., "MEM", "LTR", "RPT")
  - Description (optional)
  - Active/Inactive status
  - Display order

### 2. Tracking Number Configuration
- Format: `[PREFIX]-[YEAR]-[SERIAL]`
  - PREFIX: Custom per document type (set by admin)
  - YEAR: Auto-generated (current year, 4 digits)
  - SERIAL: Auto-increment or manual entry
- Serial number options:
  - Auto-generate: System assigns next available number
  - Manual entry: Reviewer can specify custom serial
  - Reset annually: Serial resets to 1 each year
- Uniqueness validation across all tracking numbers

### 3. Integration Points
- **Submission Form**: Document type dropdown (user selects)
- **Admin Review**: Tracking number assignment (auto or manual)
- **Search/Filter**: Filter by document type and tracking number
- **Display**: Show formatted tracking number everywhere

### 4. UI/UX Requirements
- Settings page accessible from Document Tracking admin menu
- Clear instructions for prefix format (uppercase, no spaces, 2-5 chars)
- Inline editing for document types
- Drag-and-drop reordering
- Preview of tracking number format
- Validation feedback

## Database Schema

### DocumentType Model
```python
- name: CharField (unique)
- prefix: CharField (unique, 2-5 chars, uppercase)
- description: TextField (optional)
- is_active: BooleanField
- order: IntegerField
- serial_mode: CharField (auto/manual/both)
- reset_annually: BooleanField
- created_at: DateTimeField
- updated_at: DateTimeField
```

### TrackingNumberSequence Model
```python
- document_type: ForeignKey
- year: IntegerField
- last_serial: IntegerField
- created_at: DateTimeField
- updated_at: DateTimeField
- unique_together: (document_type, year)
```

### Update Submission Model
```python
- document_type: ForeignKey (nullable for backward compatibility)
- tracking_number: CharField (indexed, unique when not null)
```

## URLs
- `/tracking/admin/settings/` - Settings page
- `/tracking/admin/settings/document-types/` - Document types management
- `/tracking/admin/settings/document-types/add/` - Add document type
- `/tracking/admin/settings/document-types/<id>/edit/` - Edit document type
- `/tracking/admin/settings/document-types/<id>/delete/` - Delete document type
- `/tracking/admin/settings/document-types/reorder/` - Reorder (AJAX)

## API Endpoints
- `POST /tracking/api/generate-tracking-number/` - Generate next tracking number
- `POST /tracking/api/validate-tracking-number/` - Validate custom tracking number
- `GET /tracking/api/document-types/` - Get active document types

## Migration Strategy
1. Create new models (DocumentType, TrackingNumberSequence)
2. Add fields to Submission model (nullable)
3. Create default document types (General, Memorandum, Letter)
4. Migrate existing submissions (assign "General" type)
5. Update forms and views
6. Update templates

## Testing Requirements
- Unit tests for tracking number generation
- Uniqueness validation tests
- Annual reset tests
- Manual entry validation tests
- Integration tests for submission workflow
- UI tests for settings page

## Security Considerations
- Only staff users can access settings
- Validate prefix format (prevent SQL injection, XSS)
- Validate serial numbers (positive integers only)
- Prevent deletion of document types with existing submissions
- Audit log for settings changes
