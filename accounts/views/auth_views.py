from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


def login_view(request):
    if request.user.is_authenticated:
        return redirect("root")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both email/username and password.")
            return render(request, "auth/login.html")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            
            # Add success message for dashboard
            messages.success(
                request, 
                f"Welcome back, {user.get_full_name() or user.username}!"
            )

            if user.login_role == "admin":
                return redirect("admin_app:main-dashboard")
            else:
                return redirect("user_app:main-dashboard")

        messages.error(request, "Invalid email/username or password. Please try again.")

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect(settings.LOGIN_URL)
