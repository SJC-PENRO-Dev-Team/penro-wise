from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Q
from accounts.models import User, WorkforcesDepartment
from accounts.forms import UserCreateForm
from django.contrib import messages
from django.db import transaction
from notifications.services.user_management import (
    notify_user_profile_updated_by_admin
)
# Removed: notify_user_account_created, notify_user_organization_changed
# Reason: Email notifications cause timeout issues for organization changes

@login_required
def users(request):
    """
    Users list view with department filtering, search, and sorting.
    Also includes department management section.
    """
    # Base queryset with department relationship
    users_qs = User.objects.select_related("department")

    # =====================================================
    # DEPARTMENT FILTER
    # =====================================================
    current_department = request.GET.get('department')

    # Get all departments for filter dropdown
    departments = WorkforcesDepartment.objects.all().order_by('name')

    # Filter by department
    department_name = None
    
    if current_department:
        users_qs = users_qs.filter(department_id=current_department)
        department_obj = WorkforcesDepartment.objects.filter(id=current_department).first()
        if department_obj:
            department_name = department_obj.name

    # =====================================================
    # SEARCH
    # =====================================================
    search_query = request.GET.get('q', '').strip()
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(position_title__icontains=search_query)
        )

    # =====================================================
    # SORTING
    # =====================================================
    current_sort = request.GET.get('sort', 'name_asc')
    
    sort_mapping = {
        'name_asc': ['first_name', 'last_name', 'username'],
        'name_desc': ['-first_name', '-last_name', '-username'],
        'date_desc': ['-date_joined'],
        'date_asc': ['date_joined'],
        'role_asc': ['login_role', 'username'],
    }
    
    sort_fields = sort_mapping.get(current_sort, ['first_name', 'last_name', 'username'])
    users_qs = users_qs.order_by(*sort_fields)

    # =====================================================
    # DEPARTMENT MANAGEMENT DATA
    # =====================================================
    # Get all departments with their member counts
    all_departments = WorkforcesDepartment.objects.all().order_by('name')
    
    # Calculate statistics for each department
    departments_with_stats = []
    for dept in all_departments:
        members = User.objects.filter(department=dept).select_related('department')
        departments_with_stats.append({
            'department': dept,
            'members': members.order_by('first_name', 'last_name'),
            'stats': {
                'total_members': members.count(),
                'total_admins': members.filter(login_role='admin').count(),
                'total_regular_users': members.filter(login_role='user').count(),
                'active_users': members.filter(is_active=True).count(),
            }
        })

    # =====================================================
    # CONTEXT
    # =====================================================
    form = UserCreateForm()

    context = {
        "users": users_qs,
        "total_users": users_qs.count(),
        "form": form,
        
        # Filter data
        "departments": departments,
        
        # Current filters
        "current_department": current_department,
        "current_department_name": department_name,
        
        # Search & Sort
        "search_query": search_query,
        "current_sort": current_sort,
        
        # Department management (multiple departments)
        "departments_with_stats": departments_with_stats,
    }

    return render(request, "admin/page/users.html", context)


@login_required
def user_profile(request, user_id):
    """
    Admin view: User Profile (view + inline edit)
    """
    user_obj = get_object_or_404(
        User.objects.select_related("department"),
        id=user_id,
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()

        # ------------------------------------
        # VALIDATE USERNAME
        # ------------------------------------
        if not username:
            messages.error(request, "Username cannot be empty.")
            return redirect("admin_app:user-profile", user_id=user_obj.id)

        if (
            User.objects
            .exclude(id=user_obj.id)
            .filter(username=username)
            .exists()
        ):
            messages.error(request, "Username is already taken.")
            return redirect("admin_app:user-profile", user_id=user_obj.id)

        # ------------------------------------
        # TRACK CHANGES
        # ------------------------------------
        changed_fields = {}
        
        new_first_name = request.POST.get("first_name", "").strip()
        new_last_name = request.POST.get("last_name", "").strip()
        new_position_title = request.POST.get("position_title", "").strip()
        
        if user_obj.username != username:
            changed_fields['username'] = username
        if user_obj.first_name != new_first_name:
            changed_fields['first_name'] = new_first_name
        if user_obj.last_name != new_last_name:
            changed_fields['last_name'] = new_last_name
        if user_obj.email != email:
            changed_fields['email'] = email
        if user_obj.position_title != new_position_title:
            changed_fields['position_title'] = new_position_title

        # ------------------------------------
        # SAVE FIELDS
        # ------------------------------------
        user_obj.username = username
        user_obj.first_name = new_first_name
        user_obj.last_name = new_last_name
        user_obj.email = email
        user_obj.position_title = new_position_title

        user_obj.save(update_fields=[
            "username",
            "first_name",
            "last_name",
            "email",
            "position_title",
        ])

        # ------------------------------------
        # SEND NOTIFICATION IF CHANGES MADE
        # ------------------------------------
        if changed_fields:
            notify_user_profile_updated_by_admin(
                user=user_obj,
                updated_by_admin=request.user,
                changed_fields=changed_fields
            )

        messages.success(request, "User profile updated successfully.")

        return redirect("admin_app:user-profile", user_id=user_obj.id)

    return render(
        request,
        "admin/page/user_profile.html",
        {
            "profile_user": user_obj,
            "is_own_profile": (request.user.id == user_obj.id),
            "departments": WorkforcesDepartment.objects.all().order_by("name"),
        }
    )

@login_required
def user_update_role(request, user_id):
    """
    Admin-only view to update user role
    """
    # Only admins can update roles
    if request.user.login_role != 'admin':
        messages.error(request, "You don't have permission to change user roles.")
        return redirect("admin_app:user-profile", user_id=user_id)

    if request.method != "POST":
        return redirect("admin_app:user-profile", user_id=user_id)

    user_obj = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("login_role", "").strip()

    # Validate role
    if new_role not in ['user', 'admin']:
        messages.error(request, "Invalid role selected.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Prevent self-demotion (admin removing their own admin role)
    if user_obj.id == request.user.id and new_role == 'user' and request.user.login_role == 'admin':
        messages.error(request, "You cannot remove your own admin privileges.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Update role
    user_obj.login_role = new_role
    user_obj.save(update_fields=["login_role"])

    messages.success(request, f"User role updated to {user_obj.get_login_role_display()}.")
    return redirect("admin_app:user-profile", user_id=user_obj.id)

@login_required
def user_update_image(request, user_id):
    """
    Update user profile image
    Can be done by admin or the user themselves
    """
    user_obj = get_object_or_404(User, id=user_id)
    
    # Permission check: admin or self
    if request.user.login_role != 'admin' and request.user.id != user_obj.id:
        messages.error(request, "You don't have permission to change this user's profile picture.")
        return redirect("admin_app:user-profile", user_id=user_id)

    if request.method != "POST":
        messages.warning(request, "Invalid request method.")
        return redirect("admin_app:user-profile", user_id=user_id)

    # Debug logging
    print(f"=== Profile Image Upload Debug ===")
    print(f"User ID: {user_id}")
    print(f"POST data: {request.POST}")
    print(f"FILES data: {request.FILES}")
    print(f"Content-Type: {request.content_type}")
    
    # Check if user wants to remove the image
    remove_image = request.POST.get('remove_image') == 'true'
    
    if remove_image:
        # Delete old image file if exists
        if user_obj.profile_image:
            user_obj.profile_image.delete(save=False)
        
        user_obj.profile_image = None
        user_obj.save(update_fields=['profile_image'])
        messages.success(request, "Profile picture removed successfully.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Handle new image upload
    profile_image = request.FILES.get('profile_image')
    
    if not profile_image:
        messages.error(request, "No image file provided. Please select an image.")
        print("ERROR: No file in request.FILES")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Validate file type
    if not profile_image.content_type.startswith('image/'):
        messages.error(request, "Please upload a valid image file.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Validate file size (5MB max)
    if profile_image.size > 5 * 1024 * 1024:
        messages.error(request, "Image file size must be less than 5MB.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)

    # Delete old image if exists
    if user_obj.profile_image:
        user_obj.profile_image.delete(save=False)

    # Save new image
    user_obj.profile_image = profile_image
    user_obj.save(update_fields=['profile_image'])

    messages.success(request, "Profile picture updated successfully.")
    print(f"SUCCESS: Image saved as {user_obj.profile_image.name}")
    return redirect("admin_app:user-profile", user_id=user_obj.id)

@login_required
def create_user(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Invalid request method."},
            status=405
        )

    form = UserCreateForm(request.POST)

    # -----------------------------
    # FORM ERRORS (PASS-THROUGH)
    # -----------------------------
    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    field: [str(e) for e in errs]
                    for field, errs in form.errors.items()
                }
            },
            status=400
        )

    try:
        with transaction.atomic():
            user = form.save()
            request.session[f"user_form_{user.id}"] = dict(request.POST)
            
            # Add success message for toast notification
            messages.success(request, f"User '{user.get_full_name() or user.username}' created successfully!")

    except IntegrityError:
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "username": ["This username or email already exists."]
                }
            },
            status=400
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "__all__": ["Unexpected server error. Please try again."]
                }
            },
            status=500
        )

    return JsonResponse(
        {
            "success": True,
            "message": f"User '{user.username}' created successfully.",
            "user_id": user.id,
            "profile_url": reverse(
                "admin_app:user-profile",
                args=[user.id]
            )
        },
        status=201
    )


@login_required
def update_department(request, department_id):
    """
    Update department name and description.
    Admin only.
    """
    if request.user.login_role != 'admin':
        messages.error(request, "You don't have permission to update department settings.")
        return redirect("admin_app:users")
    
    if request.method != "POST":
        return redirect("admin_app:users")
    
    # Get the specific department
    department = get_object_or_404(WorkforcesDepartment, id=department_id)
    
    # Update department
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    
    if not name:
        messages.error(request, "Department name cannot be empty.")
        return redirect(reverse("admin_app:users") + "#department-panel")
    
    department.name = name
    department.description = description
    department.save(update_fields=["name", "description"])
    
    messages.success(request, f"Department '{department.name}' updated successfully.")
    return redirect(reverse("admin_app:users") + "#department-panel")


@login_required
def create_department(request):
    """
    Create a new department.
    Admin only.
    """
    if request.user.login_role != 'admin':
        messages.error(request, "You don't have permission to create departments.")
        return redirect("admin_app:users")
    
    if request.method != "POST":
        return redirect("admin_app:users")
    
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    
    if not name:
        messages.error(request, "Department name cannot be empty.")
        return redirect(reverse("admin_app:users") + "#department-panel")
    
    # Check if department with same name exists
    if WorkforcesDepartment.objects.filter(name=name).exists():
        messages.error(request, f"Department '{name}' already exists.")
        return redirect(reverse("admin_app:users") + "#department-panel")
    
    # Create department
    department = WorkforcesDepartment.objects.create(
        name=name,
        description=description
    )
    
    messages.success(request, f"Department '{department.name}' created successfully.")
    return redirect(reverse("admin_app:users") + "#department-panel")


@login_required
def delete_department(request, department_id):
    """
    Delete a department.
    Admin only. Cannot delete if department has users.
    """
    if request.user.login_role != 'admin':
        messages.error(request, "You don't have permission to delete departments.")
        return redirect("admin_app:users")
    
    if request.method != "POST":
        return redirect("admin_app:users")
    
    department = get_object_or_404(WorkforcesDepartment, id=department_id)
    
    # Check if department has users
    user_count = User.objects.filter(department=department).count()
    if user_count > 0:
        messages.error(request, f"Cannot delete department '{department.name}' because it has {user_count} user(s). Please reassign users first.")
        return redirect(reverse("admin_app:users") + "#department-panel")
    
    department_name = department.name
    department.delete()
    
    messages.success(request, f"Department '{department_name}' deleted successfully.")
    return redirect(reverse("admin_app:users") + "#department-panel")


@login_required
def user_update_department(request, user_id):
    """
    Update user's department assignment.
    Admin only.
    """
    if request.user.login_role != 'admin':
        messages.error(request, "You don't have permission to assign departments.")
        return redirect("admin_app:user-profile", user_id=user_id)
    
    if request.method != "POST":
        return redirect("admin_app:user-profile", user_id=user_id)
    
    user_obj = get_object_or_404(User, id=user_id)
    department_id = request.POST.get("department", "").strip()
    
    # Allow clearing department
    if not department_id:
        user_obj.department = None
        user_obj.save(update_fields=["department"])
        messages.success(request, "Department assignment cleared.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)
    
    # Validate department exists and is active
    try:
        department = WorkforcesDepartment.objects.get(id=department_id, is_active=True)
    except WorkforcesDepartment.DoesNotExist:
        messages.error(request, "Invalid or inactive department selected.")
        return redirect("admin_app:user-profile", user_id=user_obj.id)
    
    # Update department
    user_obj.department = department
    user_obj.save(update_fields=["department"])
    
    messages.success(request, f"User assigned to {department.name}.")
    return redirect("admin_app:user-profile", user_id=user_obj.id)
