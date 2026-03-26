"""
Forms for Digital Document Tracking System.

This module contains forms for:
- Document submission
- Tracking number assignment
- Status changes
- Compliance file uploads
"""
from django import forms
from .models import Submission


class SubmissionForm(forms.ModelForm):
    """
    Form for creating new document submissions.
    Users provide title, purpose, doc_type (new), and upload files or attach links.
    """
    files = forms.FileField(
        required=False,
        help_text='Upload one or more files (optional if links are provided)'
    )
    
    class Meta:
        model = Submission
        fields = ['title', 'purpose', 'doc_type']  # Updated to use doc_type
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document title'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the purpose of this submission'
            }),
            'doc_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'doc_type': 'Select the type of document you are submitting'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular import
        from document_tracking.services.document_type_service import get_active_document_types
        
        # Set queryset for doc_type to only show active types
        self.fields['doc_type'].queryset = get_active_document_types()
        self.fields['doc_type'].required = True
        self.fields['doc_type'].empty_label = "-- Select Document Type --"
    
    def clean_title(self):
        """Validate title is not empty or whitespace."""
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Title cannot be empty or whitespace.')
        return title
    
    def clean_purpose(self):
        """Validate purpose is not empty or whitespace."""
        purpose = self.cleaned_data.get('purpose', '').strip()
        if not purpose:
            raise forms.ValidationError('Purpose cannot be empty or whitespace.')
        return purpose


class TrackingAssignmentForm(forms.Form):
    """
    Form for assigning tracking numbers to submissions.
    Supports Mode A (auto-generate) and Mode B (manual entry).
    """
    MODE_CHOICES = [
        ('auto', 'Mode A: Auto-Generate (PENRO-YYYY-XXXXX)'),
        ('manual', 'Mode B: Manual Entry'),
    ]
    
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        initial='auto',
        required=True,
        help_text='Select tracking number assignment mode'
    )
    
    manual_tracking_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tracking number (only for Manual mode)'
        }),
        help_text='Required only for Manual mode'
    )
    
    def clean(self):
        """Validate manual tracking number is provided when mode is manual."""
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        manual_number = cleaned_data.get('manual_tracking_number', '').strip()
        
        if mode == 'manual' and not manual_number:
            raise forms.ValidationError(
                'Manual tracking number is required when using Manual mode.'
            )
        
        # Validate uniqueness if manual number provided
        if mode == 'manual' and manual_number:
            if Submission.objects.filter(tracking_number=manual_number).exists():
                raise forms.ValidationError(
                    f'Tracking number "{manual_number}" already exists. Please use a unique number.'
                )
        
        return cleaned_data


class StatusChangeForm(forms.Form):
    """
    Form for changing submission status.
    Uses hidden field for status - actual selection done via action buttons in template.
    """
    new_status = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional remarks about this status change'
        }),
        required=False,
        help_text='Optional remarks'
    )
    
    def __init__(self, *args, current_status=None, **kwargs):
        """Initialize form with current status for validation."""
        super().__init__(*args, **kwargs)
        self.current_status = current_status
    
    def clean_new_status(self):
        """Validate status transition is allowed."""
        from document_tracking.legacy_services import StatusService
        
        new_status = self.cleaned_data.get('new_status')
        
        if not self.current_status:
            raise forms.ValidationError('Current status is not set.')
        
        if not StatusService.can_transition(self.current_status, new_status):
            from .workflow import StatusWorkflow
            current_label = StatusWorkflow.get_status_info(self.current_status).get('label', self.current_status)
            new_label = StatusWorkflow.get_status_info(new_status).get('label', new_status)
            raise forms.ValidationError(
                f'Cannot transition from "{current_label}" to "{new_label}". '
                f'Please follow the workflow sequence.'
            )
        
        return new_status

class ComplianceFileUploadForm(forms.Form):
    """
    Form for uploading compliance files.
    Used when submission status is 'for_compliance' or 'returned_to_sender'.
    """
    files = forms.FileField(
        required=True,
        help_text='Upload compliance files'
    )
    
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add remarks about these compliance files'
        }),
        required=False,
        help_text='Optional remarks'
    )
    
    def __init__(self, *args, submission=None, **kwargs):
        """Initialize form with submission for validation."""
        super().__init__(*args, **kwargs)
        self.submission = submission
    
    def clean(self):
        """Validate submission status allows file uploads."""
        cleaned_data = super().clean()
        
        if not self.submission:
            raise forms.ValidationError('Submission is not set.')
        
        allowed_statuses = ['for_compliance', 'returned_to_sender']
        if self.submission.status not in allowed_statuses:
            raise forms.ValidationError(
                f'Cannot upload files when status is "{self.submission.status}". '
                f'Uploads are only allowed for statuses: {", ".join(allowed_statuses)}.'
            )
        
        return cleaned_data


class RoutingOverrideForm(forms.Form):
    """
    Form for admin to manually override automatic routing.
    """
    section = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        help_text='Select section to route this submission'
    )
    
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for routing override'
        }),
        required=False,
        help_text='Optional remarks'
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize form with section queryset."""
        super().__init__(*args, **kwargs)
        from .models import Section
        self.fields['section'].queryset = Section.objects.all()



# ============================================================
# DOCUMENT TYPE MANAGEMENT FORMS (Settings)
# ============================================================

class DocumentTypeForm(forms.ModelForm):
    """
    Form for creating and editing document types.
    Used in settings page for managing custom document types.
    """
    class Meta:
        from document_tracking.models import DocumentType
        model = DocumentType
        fields = ['name', 'prefix', 'description', 'is_active', 'serial_mode', 'reset_policy']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Memorandum, Letter, Report'
            }),
            'prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MEM, LTR, RPT',
                'maxlength': '5',
                'style': 'text-transform: uppercase;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this document type'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'serial_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reset_policy': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'name': 'Document type name (must be unique)',
            'prefix': '2-5 uppercase letters only (e.g., MEM, LTR, RPT)',
            'description': 'Optional description for this document type',
            'is_active': 'Active types appear in submission forms',
            'serial_mode': 'How serial numbers are assigned',
            'reset_policy': 'When to reset the sequence counter (applies to auto mode only)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add preview field (not saved to database)
        self.fields['preview'] = forms.CharField(
            required=False,
            disabled=True,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preview will appear here',
                'readonly': 'readonly'
            }),
            help_text='Preview of tracking number format'
        )
        
        # Set initial preview if editing
        if self.instance and self.instance.pk:
            from datetime import datetime
            year = datetime.now().year
            self.fields['preview'].initial = f"{self.instance.prefix}-{year}-XXX"
    
    def clean_prefix(self):
        """Validate and normalize prefix."""
        prefix = self.cleaned_data.get('prefix', '').strip().upper()
        
        if not prefix:
            raise forms.ValidationError('Prefix is required')
        
        # Validate format
        import re
        if not re.match(r'^[A-Z]{2,5}$', prefix):
            raise forms.ValidationError(
                'Prefix must be 2-5 uppercase letters only (e.g., MEM, LTR, RPT)'
            )
        
        # Check uniqueness (exclude current instance if editing)
        from document_tracking.models import DocumentType
        query = DocumentType.objects.filter(prefix=prefix)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError(f'Prefix "{prefix}" is already in use')
        
        return prefix
    
    def clean_name(self):
        """Validate name uniqueness."""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise forms.ValidationError('Name is required')
        
        # Check uniqueness (exclude current instance if editing)
        from document_tracking.models import DocumentType
        query = DocumentType.objects.filter(name=name)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError(f'Document type "{name}" already exists')
        
        return name


class TrackingNumberAssignmentForm(forms.Form):
    """
    Form for assigning tracking numbers with new document type system.
    Replaces the old TrackingAssignmentForm.
    """
    document_type = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_document_type'
        }),
        required=True,
        help_text='Select document type for tracking number'
    )
    
    assignment_mode = forms.ChoiceField(
        choices=[
            ('auto', 'Auto-generate next number'),
            ('manual', 'Enter custom number'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='auto',
        required=True,
        help_text='Choose how to assign the tracking number'
    )
    
    manual_serial = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=999999999999,  # 12-digit maximum
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 1, 42, 100, 999999 (up to 12 digits)',
            'id': 'id_manual_serial',
            'max': '999999999999'
        }),
        help_text='Enter the serial number (1 to 999,999,999,999). Format: PREFIX-YEAR-XXXXXXXXXXXX will be generated automatically.',
        error_messages={
            'min_value': 'Serial number must be at least 1.',
            'max_value': 'Serial number cannot exceed 999,999,999,999 (12 digits).',
            'invalid': 'Please enter a valid number.'
        }
    )
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_year'
        }),
        help_text='Year for tracking number (defaults to current year)'
    )
    
    preview = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'id_preview',
            'style': 'font-weight: bold; font-size: 1.1em;'
        }),
        help_text='Preview of tracking number'
    )
    
    def __init__(self, *args, submission=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular import
        from document_tracking.services.document_type_service import get_active_document_types
        from datetime import datetime
        
        self.submission = submission
        
        # Set document type queryset
        active_types = get_active_document_types()
        self.fields['document_type'].queryset = active_types
        
        # Add prefix and serial_mode as data attributes to widget
        self.fields['document_type'].widget.attrs['data-prefixes'] = '|'.join([
            f"{dt.id}:{dt.prefix}" for dt in active_types
        ])
        self.fields['document_type'].widget.attrs['data-serial-modes'] = '|'.join([
            f"{dt.id}:{dt.serial_mode}" for dt in active_types
        ])
        
        # Set default year
        self.fields['year'].initial = datetime.now().year
        
        # If submission has doc_type, set as initial and configure form based on serial_mode
        if submission and submission.doc_type:
            self.fields['document_type'].initial = submission.doc_type
            doc_type = submission.doc_type
            
            # Configure form based on document type's serial_mode
            if doc_type.serial_mode == 'auto':
                # Auto mode only - hide assignment_mode choice and manual_serial
                self.fields['assignment_mode'].widget = forms.HiddenInput()
                self.fields['assignment_mode'].initial = 'auto'
                self.fields['manual_serial'].widget = forms.HiddenInput()
                self.fields['manual_serial'].required = False
            elif doc_type.serial_mode == 'manual':
                # Manual mode only - hide assignment_mode choice, force manual
                self.fields['assignment_mode'].widget = forms.HiddenInput()
                self.fields['assignment_mode'].initial = 'manual'
                self.fields['manual_serial'].required = True
            # else: serial_mode == 'both' - show all fields (default behavior)
    
    def clean(self):
        """Validate tracking number assignment."""
        cleaned_data = super().clean()
        
        document_type = cleaned_data.get('document_type')
        assignment_mode = cleaned_data.get('assignment_mode')
        manual_serial = cleaned_data.get('manual_serial')
        year = cleaned_data.get('year')
        
        if not document_type:
            raise forms.ValidationError('Document type is required')
        
        # Validate assignment_mode matches document_type's serial_mode
        if document_type.serial_mode == 'auto' and assignment_mode != 'auto':
            raise forms.ValidationError(
                f'Document type "{document_type.name}" is configured for auto-generation only.'
            )
        elif document_type.serial_mode == 'manual' and assignment_mode != 'manual':
            raise forms.ValidationError(
                f'Document type "{document_type.name}" is configured for manual entry only.'
            )
        
        # Validate manual serial if manual mode
        if assignment_mode == 'manual':
            if not manual_serial:
                raise forms.ValidationError('Serial number is required for manual mode')
            
            if manual_serial < 1:
                raise forms.ValidationError('Serial number must be positive')
        
        # Validate year
        from datetime import datetime
        if not year:
            year = datetime.now().year
            cleaned_data['year'] = year
        
        if not (2000 <= year <= 2100):
            raise forms.ValidationError('Year must be between 2000 and 2100')
        
        # Generate preview and validate uniqueness
        from document_tracking.services.tracking_number_service import (
            validate_tracking_number,
            format_tracking_number_preview
        )
        
        if assignment_mode == 'auto':
            # Preview with XXX for auto mode
            preview = format_tracking_number_preview(document_type, year)
            cleaned_data['preview'] = preview
        else:
            # Generate actual tracking number for manual mode
            tracking_number = document_type.format_tracking_number(year, manual_serial)
            
            # Validate uniqueness
            exclude_id = self.submission.id if self.submission else None
            validation = validate_tracking_number(tracking_number, exclude_id)
            
            if not validation['valid']:
                raise forms.ValidationError('; '.join(validation['errors']))
            
            cleaned_data['preview'] = tracking_number
        
        return cleaned_data



# ============================================================
# SECTION MANAGEMENT FORMS (Settings)
# ============================================================

class SectionForm(forms.ModelForm):
    """
    Form for creating and editing sections/departments.
    Used in settings page for managing organizational sections.
    """
    class Meta:
        from document_tracking.models import Section
        model = Section
        fields = ['name', 'display_name', 'description', 'is_active', 'officers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., licensing, enforcement, admin'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Licensing Department'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this section\'s responsibilities'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'officers': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
        }
        help_texts = {
            'name': 'Unique identifier (lowercase, no spaces)',
            'display_name': 'Name shown to users',
            'description': 'Optional description',
            'is_active': 'Active sections appear in submission forms',
            'officers': 'Users who can process submissions for this section',
        }
    
    def clean_name(self):
        """Validate name is lowercase and no spaces."""
        name = self.cleaned_data.get('name', '').strip().lower()
        
        if not name:
            raise forms.ValidationError('Name is required')
        
        # Validate format
        import re
        if not re.match(r'^[a-z0-9_-]+$', name):
            raise forms.ValidationError(
                'Name must be lowercase letters, numbers, hyphens, or underscores only'
            )
        
        # Check uniqueness (exclude current instance if editing)
        from document_tracking.models import Section
        query = Section.objects.filter(name=name)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError(f'Section "{name}" already exists')
        
        return name
    
    def clean_display_name(self):
        """Validate display name is not empty."""
        display_name = self.cleaned_data.get('display_name', '').strip()
        
        if not display_name:
            raise forms.ValidationError('Display name is required')
        
        return display_name



class WorkflowRevertForm(forms.Form):
    """
    Form for reverting workflow to a previous step.
    Admin can select which previous step to revert to and provide a reason.
    """
    target_status = forms.ChoiceField(
        label="Revert to Step",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        help_text="Select the previous step to revert to"
    )
    
    reason = forms.CharField(
        label="Reason for Revert",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explain why you are reverting this submission...',
            'required': True
        }),
        help_text="Provide a detailed reason for reverting the workflow (mandatory)"
    )
    
    def __init__(self, submission, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get available previous steps based on submission history
        from document_tracking.models import Logbook
        from document_tracking.workflow import StatusWorkflow
        
        # Get all previous statuses from logbook
        previous_statuses = Logbook.objects.filter(
            submission=submission,
            action='status_changed'
        ).values_list('old_status', 'new_status').order_by('timestamp')
        
        # Build list of unique previous statuses
        visited_statuses = set()
        for old_status, new_status in previous_statuses:
            if old_status:
                visited_statuses.add(old_status)
        
        # Create choices from visited statuses (excluding current)
        current_status = submission.status
        choices = []
        
        for status in visited_statuses:
            if status != current_status:
                status_info = StatusWorkflow.get_status_info(status)
                label = status_info.get('label', status)
                level = status_info.get('level', 0)
                choices.append((status, f"Step {level}: {label}"))
        
        # Sort by level
        choices.sort(key=lambda x: StatusWorkflow.get_status_info(x[0]).get('level', 0))
        
        if not choices:
            # If no previous statuses, allow reverting to initial state
            choices = [('pending_tracking', 'Step 1: Received/Submitted')]
        
        self.fields['target_status'].choices = choices
    
    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()
        if not reason:
            raise forms.ValidationError("Reason for revert is mandatory")
        if len(reason) < 10:
            raise forms.ValidationError("Please provide a more detailed reason (at least 10 characters)")
        return reason
