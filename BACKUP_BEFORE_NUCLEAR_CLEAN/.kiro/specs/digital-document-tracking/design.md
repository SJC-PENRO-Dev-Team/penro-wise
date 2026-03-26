# Design Document: Digital Document Tracking System

## Overview

The Digital Document Tracking System is a standalone Django application for managing document submissions, tracking, routing, and archival. The system operates independently from existing workflow systems with its own models, views, URLs, and templates.

The design follows a strict workflow sequence with deterministic status transitions, role-based permissions, and comprehensive audit logging. Files are stored in the existing file manager infrastructure but organized in dedicated paths for document tracking.

### Key Design Principles

1. **Complete Isolation**: No dependencies on workcycle/workitem models
2. **Strict Workflow**: Enforced status transition matrix
3. **Audit Trail**: Append-only logbook for all actions
4. **Role-Based Access**: User, Admin, Section Officer permissions
5. **File Manager Integration**: Use existing DocumentFolder and WorkItemAttachment infrastructure

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Tracking App                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Models     │  │    Views     │  │  Templates   │      │
│  │              │  │              │  │              │      │
│  │ - Submission │  │ - Submit     │  │ - Form       │      │
│  │ - Logbook    │  │ - List       │  │ - List       │      │
│  │ - Section    │  │ - Detail     │  │ - Detail     │      │
│  │              │  │ - Admin      │  │ - Admin      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Existing File Manager Infrastructure            │
├─────────────────────────────────────────────────────────────┤
│  - DocumentFolder (structure/models.py)                      │
│  - WorkItemAttachment (accounts/models.py)                   │
│  - File storage and retrieval                                │
└─────────────────────────────────────────────────────────────┘
```

### Application Structure

```
document_tracking/
├── __init__.py
├── models.py              # Submission, Logbook, Section
├── forms.py               # SubmissionForm, TrackingAssignmentForm
├── views.py               # User and Admin views
├── urls.py                # URL patterns
├── permissions.py         # Permission decorators
├── services.py            # Business logic (tracking, routing, archival)
├── admin.py               # Django admin configuration
├── migrations/
└── templates/
    └── document_tracking/
        ├── submit.html
        ├── list.html
        ├── detail.html
        ├── admin_list.html
        └── admin_detail.html
```

## Components and Interfaces

### Models

#### Submission Model

```python
class Submission(models.Model):
    """
    Core document submission record.
    Completely independent from WorkCycle/WorkItem.
    """
    # Identification
    tracking_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    
    # Submission Data
    title = models.CharField(max_length=255)
    purpose = models.TextField()
    document_type = models.CharField(
        max_length=20,
        choices=[
            ('permit', 'Permit'),
            ('inspection', 'Inspection'),
            ('memo', 'Memo'),
            ('others', 'Others'),
        ]
    )
    
    # Workflow
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending_tracking', 'Pending Tracking Assignment'),
            ('received', 'Received'),
            ('under_review', 'Under Review'),
            ('for_compliance', 'For Compliance'),
            ('returned_to_sender', 'Returned to Sender'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('archived', 'Archived'),
        ],
        default='pending_tracking',
        db_index=True
    )
    
    # Ownership and Routing
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='document_submissions'
    )
    assigned_section = models.ForeignKey(
        'Section',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # File Storage References
    primary_folder = models.ForeignKey(
        'structure.DocumentFolder',
        on_delete=models.PROTECT,
        related_name='primary_submissions',
        null=True,
        blank=True
    )
    archive_folder = models.ForeignKey(
        'structure.DocumentFolder',
        on_delete=models.PROTECT,
        related_name='archived_submissions',
        null=True,
        blank=True
    )
    
    # Locking
    is_locked = models.BooleanField(default=False)
    tracking_locked = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['submitted_by']),
            models.Index(fields=['tracking_number']),
        ]
```

#### Logbook Model

```python
class Logbook(models.Model):
    """
    Append-only audit trail for all submission actions.
    """
    submission = models.ForeignKey(
        'Submission',
        on_delete=models.PROTECT,
        related_name='logs'
    )
    
    action = models.CharField(
        max_length=100,
        choices=[
            ('created', 'Submission Created'),
            ('tracking_assigned', 'Tracking Assigned'),
            ('status_changed', 'Status Changed'),
            ('files_uploaded', 'Files Uploaded'),
            ('archived', 'Archived'),
        ]
    )
    
    # Action Details
    old_status = models.CharField(max_length=50, null=True, blank=True)
    new_status = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(blank=True)
    file_names = models.TextField(blank=True)  # JSON list of file names
    
    # Actor
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['submission', 'timestamp']),
        ]
```

#### Section Model

```python
class Section(models.Model):
    """
    Processing sections for document routing.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        choices=[
            ('licensing', 'Licensing'),
            ('enforcement', 'Enforcement'),
            ('admin', 'Admin'),
        ]
    )
    
    # Section Officers
    officers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='document_sections',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
```

### Services Layer

#### TrackingService

```python
class TrackingService:
    """
    Handles tracking number assignment and validation.
    """
    
    @staticmethod
    def generate_tracking_number(year: int) -> str:
        """
        Generate tracking number in format: PENRO-YYYY-XXXXX
        XXXXX is 5-digit zero-padded increment unique per year.
        """
        pass
    
    @staticmethod
    def assign_tracking_number(
        submission: Submission,
        mode: str,
        manual_number: str = None,
        actor: User = None
    ) -> None:
        """
        Assign tracking number (Mode A: auto, Mode B: manual).
        Creates logbook entry and transitions status to 'received'.
        """
        pass
    
    @staticmethod
    def validate_tracking_number(tracking_number: str) -> bool:
        """
        Validate tracking number uniqueness.
        """
        pass
```

#### RoutingService

```python
class RoutingService:
    """
    Handles automatic document routing based on document type.
    """
    
    ROUTING_MAP = {
        'permit': 'licensing',
        'inspection': 'enforcement',
        'memo': 'admin',
        'others': 'admin',
    }
    
    @staticmethod
    def route_submission(submission: Submission) -> Section:
        """
        Route submission to appropriate section based on document_type.
        """
        pass
    
    @staticmethod
    def override_routing(
        submission: Submission,
        section: Section,
        actor: User
    ) -> None:
        """
        Allow admin to manually override routing.
        """
        pass
```

#### FileService

```python
class FileService:
    """
    Handles file storage operations using existing file manager.
    """
    
    @staticmethod
    def create_primary_folder(submission: Submission) -> DocumentFolder:
        """
        Create folder at: /documents/{YEAR}/forms/{SANITIZED_TITLE}/
        Returns DocumentFolder instance.
        """
        pass
    
    @staticmethod
    def create_archive_folder(submission: Submission) -> DocumentFolder:
        """
        Create folder at: /documents/{YEAR}/archive/{TRACKING_NUMBER}/
        Returns DocumentFolder instance.
        """
        pass
    
    @staticmethod
    def store_files(
        submission: Submission,
        files: List[UploadedFile],
        folder: DocumentFolder,
        uploaded_by: User
    ) -> List[WorkItemAttachment]:
        """
        Store files in specified folder using WorkItemAttachment.
        Auto-rename duplicates.
        """
        pass
    
    @staticmethod
    def move_files_to_archive(submission: Submission) -> None:
        """
        Move all files from primary_folder to archive_folder.
        """
        pass
    
    @staticmethod
    def sanitize_folder_name(title: str) -> str:
        """
        Convert title to safe folder name.
        """
        pass
```

#### ArchivalService

```python
class ArchivalService:
    """
    Handles document archival process.
    """
    
    @staticmethod
    def archive_submission(submission: Submission, actor: User) -> None:
        """
        Archive submission:
        1. Create archive folder
        2. Move files
        3. Set status to 'archived'
        4. Lock record
        5. Create logbook entry
        """
        pass
    
    @staticmethod
    def can_archive(submission: Submission) -> bool:
        """
        Check if submission can be archived (status is 'approved' or 'rejected').
        """
        pass
```

#### StatusService

```python
class StatusService:
    """
    Handles status transitions with validation.
    """
    
    TRANSITION_MATRIX = {
        'pending_tracking': ['received'],
        'received': ['under_review'],
        'under_review': ['for_compliance', 'approved', 'rejected'],
        'for_compliance': ['under_review'],
        'returned_to_sender': ['under_review'],
        'approved': ['archived'],
        'rejected': ['archived'],
        'archived': [],  # No transitions allowed
    }
    
    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed.
        """
        pass
    
    @staticmethod
    def change_status(
        submission: Submission,
        new_status: str,
        actor: User,
        remarks: str = ""
    ) -> None:
        """
        Change submission status with validation and logging.
        """
        pass
```

### Views

#### User Views

```python
# Submit Document
def submit_document(request):
    """
    Display submission form and handle POST.
    Create submission with status 'pending_tracking'.
    Create primary folder and store files.
    Create logbook entry.
    """
    pass

# View Own Submissions
def my_submissions(request):
    """
    List all submissions by current user.
    """
    pass

# View Submission Detail
def submission_detail(request, submission_id):
    """
    Display submission details, files, and logbook.
    Allow file upload if status is 'for_compliance' or 'returned_to_sender'.
    """
    pass

# Upload Compliance Files
def upload_compliance_files(request, submission_id):
    """
    Handle additional file uploads for compliance.
    Validate status allows uploads.
    Store files in primary folder.
    Create logbook entry.
    """
    pass
```

#### Admin Views

```python
# View All Submissions
def admin_submissions(request):
    """
    List all submissions with filters (status, section, date range).
    """
    pass

# Admin Submission Detail
def admin_submission_detail(request, submission_id):
    """
    Display submission with admin actions:
    - Assign tracking number
    - Change status
    - Override routing
    - Archive
    """
    pass

# Assign Tracking Number
def assign_tracking(request, submission_id):
    """
    Handle tracking number assignment (Mode A or Mode B).
    Validate uniqueness.
    Transition status to 'received'.
    Create logbook entry.
    Auto-route to section.
    """
    pass

# Change Status
def change_status(request, submission_id):
    """
    Handle status change with validation.
    Create logbook entry.
    """
    pass

# Archive Submission
def archive_submission(request, submission_id):
    """
    Handle archival process.
    Validate status is 'approved' or 'rejected'.
    Move files to archive.
    Lock record.
    """
    pass
```

#### Section Officer Views

```python
# View Assigned Submissions
def section_submissions(request):
    """
    List submissions assigned to officer's section.
    """
    pass

# Update Status (Section Officer)
def section_update_status(request, submission_id):
    """
    Allow section officer to update status for assigned submissions.
    Validate officer belongs to assigned section.
    """
    pass
```

### Permissions

```python
def user_can_view_submission(user, submission):
    """
    User can view if they are the submitter.
    Admin can view all.
    Section officer can view assigned section.
    """
    pass

def user_can_upload_compliance(user, submission):
    """
    User can upload if:
    - They are the submitter
    - Status is 'for_compliance' or 'returned_to_sender'
    """
    pass

def user_can_assign_tracking(user):
    """
    Only admin can assign tracking numbers.
    """
    pass

def user_can_change_status(user, submission):
    """
    Admin can change any status.
    Section officer can change status for assigned section.
    """
    pass

def user_can_archive(user):
    """
    Only admin can archive.
    """
    pass
```

## Data Models

### Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                         Submission                           │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ tracking_number (UNIQUE, NULL)                               │
│ title                                                         │
│ purpose                                                       │
│ document_type (ENUM)                                         │
│ status (ENUM)                                                 │
│ submitted_by (FK → User)                                     │
│ assigned_section (FK → Section, NULL)                        │
│ primary_folder (FK → DocumentFolder, NULL)                   │
│ archive_folder (FK → DocumentFolder, NULL)                   │
│ is_locked (BOOL)                                             │
│ tracking_locked (BOOL)                                       │
│ created_at                                                    │
│ updated_at                                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 1:N
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                          Logbook                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ submission (FK → Submission)                                 │
│ action (ENUM)                                                 │
│ old_status (NULL)                                            │
│ new_status (NULL)                                            │
│ remarks                                                       │
│ file_names (JSON)                                            │
│ actor (FK → User)                                            │
│ timestamp                                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                          Section                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ name (UNIQUE, ENUM)                                          │
│ officers (M2M → User)                                        │
│ created_at                                                    │
└─────────────────────────────────────────────────────────────┘
```

### Status Transition Matrix

```
pending_tracking → received
received → under_review
under_review → for_compliance | approved | rejected
for_compliance → under_review
returned_to_sender → under_review
approved → archived
rejected → archived
archived → (no transitions)
```

### File Storage Structure

```
/documents/
└── {YEAR}/
    ├── forms/
    │   └── {SANITIZED_TITLE}/
    │       ├── file1.pdf
    │       ├── file2.docx
    │       └── compliance_file.pdf
    └── archive/
        └── {TRACKING_NUMBER}/
            ├── file1.pdf
            ├── file2.docx
            └── compliance_file.pdf
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: User Access Control

*For any* user and any submission, when the user attempts to view a submission, access should be granted only if the user is the submitter, or the user is an admin, or the user is a section officer assigned to that submission's section.

**Validates: Requirements 2.1, 2.4, 12.1**

### Property 2: Admin Capabilities

*For any* admin user and any submission, the admin should be able to view the submission, assign tracking numbers, change status to any valid value, override routing, and trigger archival when status allows.

**Validates: Requirements 2.2, 12.2, 12.3, 12.4, 12.5**

### Property 3: Section Officer Scope

*For any* section officer and any submission, the officer should be able to update status only if the submission's assigned_section matches one of the officer's sections.

**Validates: Requirements 2.3, 12.6**

### Property 4: Submission Validation

*For any* submission attempt, the submission should be rejected if title is empty/whitespace, or purpose is empty/whitespace, or document_type is not in {permit, inspection, memo, others}, or no files are uploaded. Valid submissions should have status "pending_tracking" and submitted_by equal to the authenticated user.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 5: File Storage Path Structure

*For any* submission, the primary storage folder path should match the pattern /documents/{YEAR}/forms/{SANITIZED_TITLE}/ where YEAR is the current system year and SANITIZED_TITLE contains only safe characters (alphanumeric, hyphens, underscores).

**Validates: Requirements 1.5, 4.1, 4.2, 4.3**

### Property 6: File Duplicate Handling

*For any* submission and any file upload, if a file with the same name already exists in the target folder, the new file should be stored with a modified name (e.g., appending a counter or timestamp) such that no existing file is overwritten.

**Validates: Requirements 4.4, 14.2**

### Property 7: Archive File Movement

*For any* submission that is archived, all files should exist in the archive folder at /documents/{YEAR}/archive/{TRACKING_NUMBER}/ and should not exist in the primary folder.

**Validates: Requirements 4.5, 11.2**

### Property 8: Initial Tracking Number State

*For any* newly created submission, the tracking_number field should be null and the status should be "pending_tracking".

**Validates: Requirements 5.1, 5.2**

### Property 9: Auto-Generated Tracking Number Format

*For any* submission where tracking number is assigned via Mode A (auto-generate), the tracking_number should match the format PENRO-YYYY-XXXXX where YYYY is the current year and XXXXX is a 5-digit zero-padded number, and the tracking_number should be unique across all submissions in that year.

**Validates: Requirements 5.3**

### Property 10: Tracking Number Uniqueness

*For any* tracking number assignment attempt (Mode A or Mode B), if the tracking_number already exists in the database, the assignment should be rejected with an error.

**Validates: Requirements 5.4, 5.6, 14.1**

### Property 11: Tracking Number Immutability

*For any* submission where tracking_number is not null, any attempt to modify the tracking_number field should be rejected, and the tracking_locked flag should be true.

**Validates: Requirements 5.5, 13.3**

### Property 12: Status Transition Matrix Enforcement

*For any* submission and any status change attempt, the transition should be allowed only if the current status and new status pair exists in the transition matrix:
- pending_tracking → received
- received → under_review
- under_review → {for_compliance, approved, rejected}
- for_compliance → under_review
- returned_to_sender → under_review
- approved → archived
- rejected → archived
- archived → (no transitions)

All other transitions should be rejected.

**Validates: Requirements 6.1-6.10, 7.3-7.11**

### Property 13: Valid Status Values

*For any* submission, the status field should only contain one of these values: pending_tracking, received, under_review, for_compliance, returned_to_sender, approved, rejected, archived. Any attempt to set an invalid status should be rejected.

**Validates: Requirements 7.1, 7.2**

### Property 14: Automatic Routing

*For any* submission that transitions to status "received", the assigned_section should be automatically set according to the routing map:
- permit → licensing
- inspection → enforcement
- memo → admin
- others → admin

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 15: Manual Routing Override

*For any* submission and any admin user, the admin should be able to change the assigned_section to any valid section, overriding the automatic routing.

**Validates: Requirements 8.5**

### Property 16: Logbook Entry Creation

*For any* submission action (creation, tracking assignment, status change, file upload, archival), a corresponding logbook entry should be created with the action type, timestamp, and actor user.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

### Property 17: Logbook Append-Only

*For any* submission, the count of logbook entries should never decrease over time, and existing logbook entries should never be modified or deleted.

**Validates: Requirements 9.6**

### Property 18: Logbook Completeness

*For any* logbook entry, the entry should have a non-null timestamp and a non-null actor user.

**Validates: Requirements 9.7**

### Property 19: Compliance File Upload Authorization

*For any* submission and any user, the user should be able to upload additional files only if:
- The user is the submitter (submitted_by equals user)
- The status is either "for_compliance" or "returned_to_sender"

All other upload attempts should be rejected.

**Validates: Requirements 10.1, 10.2, 10.7**

### Property 20: Compliance File Storage Location

*For any* compliance file upload, the files should be stored in the same primary_folder as the original submission files.

**Validates: Requirements 10.3**

### Property 21: Compliance Upload Tracking Stability

*For any* submission, uploading compliance files should not change the tracking_number value.

**Validates: Requirements 10.6**

### Property 22: Archival Preconditions

*For any* submission, archival should only be allowed when the status is "approved" or "rejected". Attempting to archive a submission with any other status should be rejected.

**Validates: Requirements 11.1**

### Property 23: Archival Effects

*For any* submission that is archived, the following should all be true:
- status equals "archived"
- is_locked equals true
- all files moved to archive_folder
- all logbook entries preserved
- a logbook entry with action "archived" exists

**Validates: Requirements 11.3, 11.4, 11.5, 11.6**

### Property 24: No Hard Deletes

*For any* submission, once created, the submission record should never be deleted from the database (no hard deletes). Archived submissions should remain queryable.

**Validates: Requirements 13.1, 11.6**

### Property 25: Submitted By Immutability

*For any* submission, the submitted_by field should never change after the submission is created.

**Validates: Requirements 13.4**

### Property 26: File Size Validation

*For any* file upload attempt, if the file size exceeds the configured maximum size limit, the upload should be rejected with an error.

**Validates: Requirements 14.3**

## Error Handling

### Validation Errors

All validation errors should return clear, user-friendly error messages:
- "Title cannot be empty"
- "Purpose is required"
- "Invalid document type"
- "At least one file must be uploaded"
- "Tracking number already exists"
- "Invalid status transition"
- "You do not have permission to perform this action"

### File Operation Errors

File operations should handle errors gracefully:
- **File size exceeded**: Reject upload with error message
- **Duplicate file name**: Auto-rename with counter (file_1.pdf, file_2.pdf)
- **Storage failure**: Log error and notify admin
- **Missing folder**: Auto-create folder structure

### Permission Errors

Unauthorized access attempts should:
- Return HTTP 403 Forbidden
- Log the security violation with user, action, and timestamp
- Display user-friendly error message

### Email Notification Failures

Email failures should not block operations:
- Log the error with full details
- Continue with the operation
- Optionally retry with exponential backoff

### Database Errors

Database errors should be handled with:
- Transaction rollback
- Error logging
- User-friendly error message
- Admin notification for critical errors

## Testing Strategy

### Dual Testing Approach

The system requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of valid submissions
- Edge cases (empty strings, boundary values)
- Error conditions (invalid status, unauthorized access)
- Integration points (file manager, user authentication)

**Property-Based Tests** focus on:
- Universal properties across all inputs
- Randomized test data generation
- Comprehensive input coverage

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `# Feature: digital-document-tracking, Property N: [property text]`

**Example Property Test Structure**:

```python
from hypothesis import given, strategies as st
import pytest

@given(
    title=st.text(min_size=1, max_size=255),
    purpose=st.text(min_size=1),
    document_type=st.sampled_from(['permit', 'inspection', 'memo', 'others']),
)
@pytest.mark.property_test
def test_submission_validation_property(title, purpose, document_type):
    """
    Feature: digital-document-tracking, Property 4: Submission Validation
    
    For any submission attempt, valid submissions should be created with
    correct initial state.
    """
    # Test implementation
    pass
```

### Test Coverage Requirements

**Models**:
- Submission model validation
- Logbook entry creation
- Section assignment

**Services**:
- TrackingService: number generation, assignment, validation
- RoutingService: automatic routing, manual override
- FileService: folder creation, file storage, duplicate handling
- ArchivalService: archival process, file movement
- StatusService: transition validation, status changes

**Views**:
- User submission flow
- Admin tracking assignment
- Status updates
- File uploads
- Archival process

**Permissions**:
- User access control
- Admin capabilities
- Section officer scope

### Integration Tests

Integration tests should verify:
- End-to-end submission workflow
- File storage and retrieval
- Status transitions with logbook entries
- Archival process with file movement
- Permission enforcement across views

### Test Data Generation

Use factories for test data:
- UserFactory (User, Admin, Section Officer)
- SubmissionFactory (various states)
- SectionFactory
- DocumentFolderFactory

### Continuous Testing

- Run unit tests on every commit
- Run property tests nightly (due to longer execution time)
- Maintain test coverage above 90%
- Monitor test execution time
