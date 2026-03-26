# Requirements Document: Digital Document Tracking System

## Introduction

The Digital Document Tracking System is a fully standalone module for managing document submissions, tracking, routing, processing, and archival.

This system:
- Operates independently from all existing workflow systems
- Uses its own database tables
- Uses its own URLs, views, templates, and storage paths
- Does not reference or import any existing workflow logic

The system enforces a strictly defined workflow sequence and status transition model. No undefined behaviors are permitted.

## Glossary

- **System**: The Digital Document Tracking System
- **User**: A person who submits and views their own documents
- **Admin**: A person with full system access including tracking assignment and archival
- **Section_Officer**: A person who can update document status for their assigned section only
- **Submission**: A document submission record created by a User
- **Tracking_Number**: A unique identifier assigned to a Submission by an Admin
- **Document_Type**: One of: Permit, Inspection, Memo, Others
- **Status**: The current workflow state of a Submission
- **Logbook**: Append-only audit trail of actions
- **Primary_Storage**: /documents/{YEAR}/forms/{SANITIZED_TITLE}/
- **Archive_Storage**: /documents/{YEAR}/archive/{TRACKING_NUMBER}/
- **File_Manager**: Storage infrastructure used for file operations only
- **Section**: One of: Licensing, Enforcement, Admin

## Requirements

### Requirement 1: System Isolation

**User Story:** As a system architect, I want the Digital Document Tracking System to be completely isolated from existing workflow systems, so that it operates independently without dependencies or conflicts.

#### Acceptance Criteria

1. THE System SHALL use its own database tables with no foreign key references to workcycle, workitem, workassignment, or workitemattachment tables
2. THE System SHALL use its own URL patterns that do not overlap with existing workflow URLs
3. THE System SHALL use its own view functions that do not import or call existing workflow logic
4. THE System SHALL use its own templates that do not extend or include existing workflow templates
5. THE System SHALL use its own storage paths under /documents/ that do not overlap with existing storage paths

### Requirement 2: User Role Management

**User Story:** As a system administrator, I want to define three distinct user roles with specific permissions, so that access control is properly enforced.

#### Acceptance Criteria

1. WHEN a User is authenticated, THE System SHALL allow them to submit documents and view only their own submissions
2. WHEN an Admin is authenticated, THE System SHALL allow them to view all submissions, assign tracking numbers, change status, and archive documents
3. WHEN a Section_Officer is authenticated, THE System SHALL allow them to update status only for submissions assigned to their section
4. WHEN an unauthorized user attempts to access a resource, THE System SHALL return an error and deny access

### Requirement 3: Document Submission Form

**User Story:** As a User, I want to submit documents with required information, so that my submission can be tracked and processed.

#### Acceptance Criteria

1. WHEN a User accesses the submission form, THE System SHALL display only these fields: Title, Purpose, Document_Type, and File Upload
2. WHEN a User submits the form, THE System SHALL validate that Title is a non-empty string
3. WHEN a User submits the form, THE System SHALL validate that Purpose is a non-empty text field
4. WHEN a User submits the form, THE System SHALL validate that Document_Type is one of: Permit, Inspection, Memo, or Others
5. WHEN a User submits the form, THE System SHALL validate that at least one file is uploaded
6. WHEN a User submits the form, THE System SHALL automatically set submitted_by to the authenticated user without displaying it as a form field
7. WHEN a User submits the form with valid data, THE System SHALL create a new Submission with status "Pending Tracking Assignment"
8. THE System SHALL NOT include Name, Email, or Contact Number fields in the submission form

### Requirement 4: File Storage Structure

**User Story:** As a system administrator, I want files to be stored in the file manager with an organized directory structure, so that they are easy to locate and manage.

#### Acceptance Criteria

1. WHEN a Submission is created, THE System SHALL store uploaded files in the File_Manager at Primary_Storage path /documents/{YEAR}/forms/{SANITIZED_TITLE}/
2. WHEN storing files, THE System SHALL use the current system year for the {YEAR} placeholder
3. WHEN storing files, THE System SHALL convert the Submission title to a safe folder name for {SANITIZED_TITLE}
4. WHEN a file name already exists in the storage location, THE System SHALL automatically rename the new file to avoid overwriting
5. WHEN a Submission is archived, THE System SHALL move files in the File_Manager from Primary_Storage to Archive_Storage at /documents/{YEAR}/archive/{TRACKING_NUMBER}/
6. THE System SHALL use the existing File_Manager infrastructure for all file operations including upload, storage, retrieval, and movement

### Requirement 5: Tracking Number Assignment

**User Story:** As an Admin, I want to assign tracking numbers to submissions, so that each document can be uniquely identified and tracked.

#### Acceptance Criteria

1. WHEN a Submission is created, THE System SHALL NOT generate a tracking number automatically
2. WHEN a Submission is created, THE System SHALL set the initial status to "Pending Tracking Assignment"
3. WHEN an Admin assigns a tracking number in Mode A (Auto Generate), THE System SHALL generate a tracking number in format PENRO-YYYY-XXXXX where YYYY is the current year and XXXXX is a 5-digit zero-padded increment unique per year
4. WHEN an Admin assigns a tracking number in Mode B (Manual Entry), THE System SHALL validate that the entered tracking number is unique across all submissions
5. WHEN an Admin assigns a tracking number, THE System SHALL lock the tracking number field to prevent future modifications
6. WHEN a duplicate tracking number is detected, THE System SHALL reject the assignment and display an error message

### Requirement 6: Workflow Sequence Enforcement

**User Story:** As a system administrator, I want the workflow to follow a strict sequence of steps, so that all submissions are processed consistently.

#### Acceptance Criteria

1. WHEN a Submission is created, THE System SHALL set status to "Online Submission" (step 1)
2. WHEN an Admin assigns a tracking number, THE System SHALL transition status to "Tracking Assignment" (step 2)
3. WHEN tracking assignment is complete, THE System SHALL automatically transition status to "Received" (step 3)
4. WHEN status transitions to "Received", THE System SHALL automatically create a Logbook entry (step 4)
5. WHEN status transitions to "Received", THE System SHALL automatically route the Submission to the appropriate Section (step 5)
6. WHILE a Submission is in Section Processing (step 6), THE System SHALL allow status changes between "Under Review", "For Compliance", and "Returned to Sender"
7. WHEN Section Processing is complete, THE System SHALL allow status transition to "Approved" or "Rejected" (step 7)
8. WHEN an Admin triggers archive, THE System SHALL move files and set status to "Archived" (step 8)
9. WHEN archival is complete, THE System SHALL create a final Logbook entry (step 9)
10. THE System SHALL NOT allow any workflow steps to be skipped or reordered

### Requirement 7: Status Value Management

**User Story:** As a developer, I want status values to be strictly defined with explicit transition rules, so that the workflow remains predictable and consistent.

#### Acceptance Criteria

1. THE System SHALL only allow status values from this list: Pending Tracking Assignment, Received, Under Review, For Compliance, Returned to Sender, Approved, Rejected, Archived
2. WHEN a status change is requested with an invalid value, THE System SHALL reject the change and return an error
3. WHEN status is "Pending Tracking Assignment", THE System SHALL only allow transition to "Received"
4. WHEN status is "Received", THE System SHALL only allow transition to "Under Review"
5. WHEN status is "Under Review", THE System SHALL only allow transitions to "For Compliance", "Approved", or "Rejected"
6. WHEN status is "For Compliance", THE System SHALL only allow transition to "Under Review"
7. WHEN status is "Returned to Sender", THE System SHALL only allow transition to "Under Review"
8. WHEN status is "Approved", THE System SHALL only allow transition to "Archived"
9. WHEN status is "Rejected", THE System SHALL only allow transition to "Archived"
10. WHEN status is "Archived", THE System SHALL NOT allow any status transitions
11. THE System SHALL reject any status transition not explicitly defined above

### Requirement 8: Document Routing Rules

**User Story:** As an Admin, I want documents to be automatically routed to the correct section based on document type, so that processing is efficient.

#### Acceptance Criteria

1. WHEN a Submission has Document_Type "Permit", THE System SHALL route it to the Licensing section
2. WHEN a Submission has Document_Type "Inspection", THE System SHALL route it to the Enforcement section
3. WHEN a Submission has Document_Type "Memo", THE System SHALL route it to the Admin section
4. WHEN a Submission has Document_Type "Others", THE System SHALL route it to the Admin section
5. WHEN an Admin manually overrides routing, THE System SHALL allow the override and update the assigned section

### Requirement 9: Logbook Audit Trail

**User Story:** As a compliance officer, I want a complete audit trail of all actions, so that I can track the history of each submission.

#### Acceptance Criteria

1. WHEN a Submission is created, THE System SHALL create a Logbook entry with action "Submission created", timestamp, and acting user
2. WHEN a Tracking_Number is assigned, THE System SHALL create a Logbook entry with action "Tracking assigned", timestamp, and acting user
3. WHEN a Status is changed, THE System SHALL create a Logbook entry with action "Status changed", old status, new status, timestamp, and acting user
4. WHEN files are uploaded for compliance, THE System SHALL create a Logbook entry with action "Files uploaded", file names, timestamp, and acting user
5. WHEN a Submission is archived, THE System SHALL create a Logbook entry with action "Archived", timestamp, and acting user
6. THE System SHALL never delete or overwrite existing Logbook entries
7. THE System SHALL store all Logbook entries with timestamp and acting user for full audit trail

### Requirement 10: Compliance File Upload

**User Story:** As a User, I want to upload additional files when my submission requires compliance, so that I can provide requested documentation.

#### Acceptance Criteria

1. WHEN a Submission status is "For Compliance", THE System SHALL allow the submitting User to upload additional files
2. WHEN a Submission status is "Returned to Sender", THE System SHALL allow the submitting User to upload additional files
3. WHEN a User uploads compliance files, THE System SHALL store them in the File_Manager at the same Primary_Storage folder as the original submission
4. WHEN a User uploads compliance files, THE System SHALL allow the User to add remarks
5. WHEN a User uploads compliance files, THE System SHALL create a Logbook entry for each upload
6. WHEN a User uploads compliance files, THE System SHALL NOT create a new Tracking_Number
7. WHEN a Submission status is not "For Compliance" or "Returned to Sender", THE System SHALL prevent file uploads by the User

### Requirement 11: Document Archival

**User Story:** As an Admin, I want to archive approved or rejected documents, so that they are preserved and locked from further modification.

#### Acceptance Criteria

1. WHEN a Submission status is "Approved" or "Rejected", THE System SHALL allow an Admin to trigger archival
2. WHEN an Admin triggers archival, THE System SHALL move all files in the File_Manager from Primary_Storage to Archive_Storage
3. WHEN an Admin triggers archival, THE System SHALL set the Submission status to "Archived"
4. WHEN a Submission is archived, THE System SHALL lock the record to read-only mode
5. WHEN a Submission is archived, THE System SHALL preserve all Logbook entries
6. THE System SHALL NOT allow deletion of archived Submissions
7. THE System SHALL NOT allow archival when status is "Completed"

### Requirement 12: Permission Enforcement

**User Story:** As a security administrator, I want permissions to be strictly enforced, so that unauthorized access is prevented.

#### Acceptance Criteria

1. WHEN a User attempts to view a Submission, THE System SHALL only allow access if the User is the submitter
2. WHEN an Admin attempts to view any Submission, THE System SHALL allow access
3. WHEN an Admin attempts to assign a Tracking_Number, THE System SHALL allow the action
4. WHEN an Admin attempts to change Status, THE System SHALL allow the action
5. WHEN an Admin attempts to archive a Submission, THE System SHALL allow the action
6. WHEN a Section_Officer attempts to update Status, THE System SHALL only allow the action if the Submission is assigned to their section
7. WHEN an unauthorized user attempts any restricted action, THE System SHALL return an error and deny access

### Requirement 13: Data Integrity Rules

**User Story:** As a database administrator, I want data integrity rules enforced, so that the system maintains consistent and reliable data.

#### Acceptance Criteria

1. THE System SHALL NOT perform hard deletes on any Submission records
2. THE System SHALL NOT use cascade deletes on any related records
3. WHEN a Tracking_Number is assigned, THE System SHALL prevent any modification to that Tracking_Number
4. WHEN a Submission is created, THE System SHALL prevent modification of the submitted_by field
5. THE System SHALL maintain a full audit trail in the Logbook for all actions

### Requirement 14: Edge Case Handling

**User Story:** As a system administrator, I want edge cases to be handled gracefully, so that the system remains stable and predictable.

#### Acceptance Criteria

1. WHEN a duplicate Tracking_Number is detected, THE System SHALL reject the assignment and display an error message
2. WHEN a duplicate file name is detected during upload, THE System SHALL automatically rename the file to avoid overwriting
3. WHEN a file exceeds the maximum size limit, THE System SHALL reject the upload and display an error message
4. WHEN an email notification fails to send, THE System SHALL log the error without crashing the application
5. WHEN an unauthorized user attempts to modify a Submission, THE System SHALL reject the attempt and log the security violation

### Requirement 15: System Constraints

**User Story:** As a project manager, I want the system to adhere strictly to defined requirements, so that scope creep is prevented.

#### Acceptance Criteria

1. THE System SHALL NOT merge functionality with existing workcycle or workitem systems
2. THE System SHALL NOT auto-generate Tracking_Numbers at the submission stage
3. THE System SHALL NOT allow Users to define their own Tracking_Numbers
4. THE System SHALL NOT skip Logbook entry creation for any tracked action
5. THE System SHALL NOT add workflow steps beyond those defined in Requirement 6
6. THE System SHALL NOT use status values beyond those defined in Requirement 7
7. THE System SHALL NOT implement routing logic beyond that defined in Requirement 8
