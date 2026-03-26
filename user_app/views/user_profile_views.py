from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Q
from accounts.models import User, WorkforcesDepartment
from accounts.forms import UserCreateForm
from django.contrib import messages
from notifications.services.user_management import (
    notify_admins_user_profile_updated,
    notify_user_password_changed,
    notify_admins_user_password_changed
)

@login_required
def user_profile(request):
    """
    User profile (view + edit) for the logged-in user.
    Uses the user-specific profile template.
    Users can only edit basic info and password, not org/role.
    """

    user_obj = (
        User.objects
        .select_related("department")
        .get(id=request.user.id)
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if not username:
            messages.error(request, "Username cannot be empty.")
            return redirect("user_app:profile")

        if (
            User.objects
            .exclude(id=user_obj.id)
            .filter(username=username)
            .exists()
        ):
            messages.error(request, "Username is already taken.")
            return redirect("user_app:profile")

        # -----------------------------
        # TRACK CHANGES
        # -----------------------------
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

        # -----------------------------
        # SAVE
        # -----------------------------
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

        # -----------------------------
        # SEND NOTIFICATION IF CHANGES MADE
        # -----------------------------
        if changed_fields:
            try:
                notify_admins_user_profile_updated(
                    user=user_obj,
                    updated_by_user=user_obj,
                    changed_fields=changed_fields
                )
            except Exception as e:
                print(f"Profile update notification error: {e}")

        messages.success(request, "Profile updated successfully.")
        return redirect("user_app:profile")

    # Use shared profile template
    return render(
        request,
        "user/page/user_profile.html",
        {
            "profile_user": user_obj,
            "is_own_profile": True,
            "back_url": "user_app:main-dashboard",
            "divisions": [],  # Empty for regular users
        }
    )

@login_required
def user_update_image(request):
    """
    Update logged-in user's profile image.
    No user_id, no URL parameters.
    """

    user_obj = request.user

    if request.method != "POST":
        return redirect("user_app:profile")

    # -----------------------------
    # REMOVE IMAGE
    # -----------------------------
    if request.POST.get("remove_image") == "true":
        if user_obj.profile_image:
            user_obj.profile_image.delete(save=False)

        user_obj.profile_image = None
        user_obj.save(update_fields=["profile_image"])

        messages.success(request, "Profile picture removed successfully.")
        return redirect("user_app:profile")

    # -----------------------------
    # UPLOAD NEW IMAGE
    # -----------------------------
    profile_image = request.FILES.get("profile_image")

    if not profile_image:
        messages.error(request, "No image file provided.")
        return redirect("user_app:profile")

    if not profile_image.content_type.startswith("image/"):
        messages.error(request, "Please upload a valid image file.")
        return redirect("user_app:profile")

    if profile_image.size > 5 * 1024 * 1024:
        messages.error(request, "Image file size must be less than 5MB.")
        return redirect("user_app:profile")

    if user_obj.profile_image:
        user_obj.profile_image.delete(save=False)

    user_obj.profile_image = profile_image
    user_obj.save(update_fields=["profile_image"])

    messages.success(request, "Profile picture updated successfully.")
    return redirect("user_app:profile")


@login_required
def user_reset_password(request):
    """
    Allow user to reset their own password.
    """
    if request.method != "POST":
        return redirect("user_app:profile")
    
    new_password = request.POST.get("new_password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()
    
    # Validation
    if not new_password or not confirm_password:
        messages.error(request, "Please fill in all password fields.")
        return redirect("user_app:profile")
    
    if new_password != confirm_password:
        messages.error(request, "Passwords do not match.")
        return redirect("user_app:profile")
    
    if len(new_password) < 8:
        messages.error(request, "Password must be at least 8 characters long.")
        return redirect("user_app:profile")
    
    # Update password
    request.user.set_password(new_password)
    request.user.save()
    
    # Re-authenticate to keep user logged in
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    
    # Send notifications
    try:
        notify_user_password_changed(request.user)
        notify_admins_user_password_changed(request.user)
    except Exception as e:
        print(f"Password change notification error: {e}")
    
    messages.success(request, "Password changed successfully.")
    return redirect("user_app:profile")
