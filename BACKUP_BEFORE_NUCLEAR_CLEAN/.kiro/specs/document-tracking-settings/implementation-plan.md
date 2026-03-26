# Document Tracking Settings - Implementation Plan

## Phase 1: Database Models & Migrations

### Step 1.1: Create DocumentType Model
**File**: `document_tracking/models.py`
- Add DocumentType model with all fields
- Add validation for prefix format
- Add ordering and active status
- Add __str__ method

### Step 1.2: Create TrackingNumberSequence Model
**File**: `document_tracking/models.py`
- Add TrackingNumberSequence model
- Add unique constraint on (document_type, year)
- Add method to get next serial number
- Add method to reset sequence

### Step 1.3: Update Submission Model
**File**: `document_tracking/models.py`
- Add document_type ForeignKey (nullable)
- Add tracking_number CharField (unique, indexed, nullable)
- Add validation for tracking_number format
- Update __str__ to include tracking number

### Step 1.4: Create Migration
```bash
python manage.py makemigrations document_tracking
python manage.py migrate
```

### Step 1.5: Create Default Data
**File**: `document_tracking/management/commands/create_default_document_types.py`
- Create command to add default document types
- General (GEN), Memorandum (MEM), Letter (LTR), Report (RPT)

## Phase 2: Services & Business Logic

### Step 2.1: Tracking Number Service
**File**: `document_tracking/services/tracking_number_service.py`
- `generate_tracking_number(document_type, year=None, serial=None)`
- `validate_tracking_number(tracking_number)`
- `parse_tracking_number(tracking_number)` → (prefix, year, serial)
- `get_next_serial(document_type, year)`
- `is_tracking_number_unique(tracking_number, exclude_id=None)`

### Step 2.2: Document Type Service
**File**: `document_tracking/services/document_type_service.py`
- `get_active_document_types()`
- `reorder_document_types(type_ids)`
- `can_delete_document_type(document_type_id)`

## Phase 3: Forms

### Step 3.1: Document Type Form
**File**: `document_tracking/forms.py`
- DocumentTypeForm with validation
- Prefix validation (uppercase, 2-5 chars, alphanumeric)
- Name uniqueness validation

### Step 3.2: Update Submission Form
**File**: `document_tracking/forms.py`
- Add document_type field to SubmissionForm
- Make it required for new submissions
- Add help text

### Step 3.3: Tracking Number Assignment Form
**File**: `document_tracking/forms.py`
- TrackingNumberForm for admin review
- Auto-generate or manual entry
- Validation against existing numbers

## Phase 4: Views

### Step 4.1: Settings Views
**File**: `document_tracking/views/settings_views.py`
- `settings_index` - Main settings page
- `document_types_list` - List all document types
- `document_type_add` - Add new document type
- `document_type_edit` - Edit document type
- `document_type_delete` - Delete document type (with validation)
- `document_types_reorder` - AJAX reorder

### Step 4.2: API Views
**File**: `document_tracking/views/api_views.py`
- `api_generate_tracking_number` - Generate next number
- `api_validate_tracking_number` - Validate custom number
- `api_document_types` - Get active types (JSON)

### Step 4.3: Update Existing Views
**File**: `document_tracking/views.py`
- Update `submit_document` to include document_type
- Update `admin_review` to assign tracking number
- Update `admin_list` to filter by document type
- Update search to include tracking number

## Phase 5: Templates

### Step 5.1: Settings Templates
**Files**:
- `templates/document_tracking/settings/index.html` - Settings home
- `templates/document_tracking/settings/document_types.html` - Manage types
- `templates/document_tracking/settings/document_type_form.html` - Add/Edit form

### Step 5.2: Update Existing Templates
- `templates/document_tracking/submit.html` - Add document type dropdown
- `templates/document_tracking/admin_detail.html` - Add tracking number assignment
- `templates/document_tracking/admin_list.html` - Add document type filter
- `templates/document_tracking/my_submissions.html` - Show tracking number

### Step 5.3: Components
- `templates/document_tracking/components/tracking_number_badge.html` - Display badge
- `templates/document_tracking/components/document_type_badge.html` - Type badge

## Phase 6: URLs

### Step 6.1: Settings URLs
**File**: `document_tracking/urls.py`
```python
# Settings
path('admin/settings/', settings_index, name='settings'),
path('admin/settings/document-types/', document_types_list, name='document-types'),
path('admin/settings/document-types/add/', document_type_add, name='document-type-add'),
path('admin/settings/document-types/<int:pk>/edit/', document_type_edit, name='document-type-edit'),
path('admin/settings/document-types/<int:pk>/delete/', document_type_delete, name='document-type-delete'),
path('admin/settings/document-types/reorder/', document_types_reorder, name='document-types-reorder'),

# API
path('api/generate-tracking-number/', api_generate_tracking_number, name='api-generate-tracking'),
path('api/validate-tracking-number/', api_validate_tracking_number, name='api-validate-tracking'),
path('api/document-types/', api_document_types, name='api-document-types'),
```

## Phase 7: Admin Integration

### Step 7.1: Django Admin
**File**: `document_tracking/admin.py`
- Register DocumentType model
- Register TrackingNumberSequence model (read-only)
- Update Submission admin to show tracking number

### Step 7.2: Navigation
**File**: `templates/admin/layout/header.html`
- Add "Settings" link to Document Tracking dropdown

## Phase 8: Testing

### Step 8.1: Unit Tests
**File**: `document_tracking/tests/test_tracking_number_service.py`
- Test tracking number generation
- Test uniqueness validation
- Test annual reset
- Test manual entry validation

### Step 8.2: Integration Tests
**File**: `document_tracking/tests/test_settings_views.py`
- Test document type CRUD
- Test reordering
- Test deletion validation

### Step 8.3: End-to-End Tests
- Test full submission workflow with tracking numbers
- Test search and filtering
- Test tracking number display

## Phase 9: Data Migration

### Step 9.1: Migration Script
**File**: `document_tracking/management/commands/migrate_tracking_numbers.py`
- Create "General" document type if not exists
- Assign all existing submissions to "General"
- Generate tracking numbers for existing submissions (optional)

## Phase 10: Documentation

### Step 10.1: User Guide
**File**: `DOCUMENT_TRACKING_SETTINGS_GUIDE.md`
- How to configure document types
- How to set up tracking number prefixes
- How to assign tracking numbers
- How to search by tracking number

### Step 10.2: Admin Guide
**File**: `DOCUMENT_TRACKING_ADMIN_GUIDE.md`
- Settings page overview
- Best practices for prefix naming
- Managing document types
- Troubleshooting

## Implementation Order

1. **Phase 1**: Database models and migrations (foundation)
2. **Phase 2**: Services and business logic (core functionality)
3. **Phase 3**: Forms (data validation)
4. **Phase 4**: Views (request handling)
5. **Phase 5**: Templates (UI)
6. **Phase 6**: URLs (routing)
7. **Phase 7**: Admin integration (management)
8. **Phase 8**: Testing (quality assurance)
9. **Phase 9**: Data migration (backward compatibility)
10. **Phase 10**: Documentation (user support)

## Estimated Timeline
- Phase 1-2: 2-3 hours
- Phase 3-4: 2-3 hours
- Phase 5-6: 2-3 hours
- Phase 7-8: 1-2 hours
- Phase 9-10: 1 hour
- **Total**: 8-12 hours

## Dependencies
- Django 5.2+
- Existing document_tracking app
- Bootstrap 5 (for UI)
- Font Awesome (for icons)

## Risks & Mitigation
1. **Risk**: Breaking existing submissions
   - **Mitigation**: Make all new fields nullable, provide migration script
2. **Risk**: Tracking number conflicts
   - **Mitigation**: Database unique constraint, validation before save
3. **Risk**: Performance with large datasets
   - **Mitigation**: Index tracking_number field, optimize queries
4. **Risk**: User confusion with new fields
   - **Mitigation**: Clear instructions, help text, tooltips
