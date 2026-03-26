from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User, WorkforcesDepartment


# ============================================================
# USER CREATE FORM
# ============================================================

class UserCreateForm(forms.ModelForm):
    # ----------------------------
    # PASSWORD FIELDS
    # ----------------------------
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Min. 8 characters",
        }),
        strip=False,
        required=True,
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Re-enter password",
        }),
        strip=False,
        required=True,
    )

    # ----------------------------
    # DEPARTMENT FIELD
    # ----------------------------
    department = forms.ModelChoiceField(
        queryset=WorkforcesDepartment.objects.filter(is_active=True),
        required=False,  # Optional during creation
        empty_label="No Department (Assign Later)",
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
        help_text="Assign user to a department (optional)"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "position_title",
            "login_role",
            "department",  # Added department field
        ]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "e.g. john.doe",
            }),
            "first_name": forms.TextInput(attrs={
                "placeholder": "Juan",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Dela Cruz",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "email@example.com",
            }),
            "position_title": forms.TextInput(attrs={
                "placeholder": "e.g. Manager (optional)",
            }),
            "login_role": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    # ----------------------------
    # INIT: APPLY CSS CLASSES
    # ----------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    # ----------------------------
    # VALIDATION
    # ----------------------------
    def clean_username(self):
        username = (
            self.cleaned_data
            .get("username", "")
            .strip()
            .lower()
        )

        if len(username) < 3:
            raise ValidationError(
                "Username must be at least 3 characters long."
            )

        # Case-insensitive + ignore inactive users
        if User.objects.filter(
            username__iexact=username,
            is_active=True,
        ).exists():
            raise ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = (
            self.cleaned_data
            .get("email", "")
            .strip()
            .lower()
        )

        if email and User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).exists():
            raise ValidationError(
                "This email is already registered."
            )

        return email

    def clean(self):
        cleaned = super().clean()

        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")

        # Attach errors to fields (AJAX + toast friendly)
        if not password or not confirm:
            self.add_error(
                "password",
                "Password and confirmation are required."
            )
            return cleaned

        if password != confirm:
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )
            return cleaned

        if len(password) < 8:
            self.add_error(
                "password",
                "Password must be at least 8 characters long."
            )

        return cleaned

    def clean_department(self):
        """Validate department is active if provided."""
        department = self.cleaned_data.get('department')
        
        if department and not department.is_active:
            raise ValidationError(
                "Cannot assign user to an inactive department."
            )
        
        return department

    # ----------------------------
    # SAVE
    # ----------------------------
    def save(self, commit=True):
        user = super().save(commit=False)

        # Normalize
        user.username = user.username.lower()
        user.email = (user.email or "").lower()

        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


# ============================================================
# USER UPDATE FORM
# ============================================================

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "position_title",
            "login_role",
            "is_active",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "placeholder": "First name"
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Last name"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "email@example.com"
            }),
            "position_title": forms.TextInput(attrs={
                "placeholder": "Job title"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


# ============================================================
# WORKFORCES DEPARTMENT FORM
# ============================================================

class WorkforcesDepartmentForm(forms.ModelForm):
    class Meta:
        model = WorkforcesDepartment
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Department name",
                "class": "form-control"
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Optional description",
                "class": "form-control",
                "rows": 3
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

