from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator

from notifications.models import Notification


@login_required
def user_notifications(request):
    """User notifications page with category filtering."""
    # Extra safety: prevent admins from using user UI
    if request.user.login_role != "user":
        return render(request, "403.html", status=403)

    # Optional filters
    category = request.GET.get("category")
    unread_only = request.GET.get("unread")

    qs = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("work_item", "workcycle")
    )

    if category:
        qs = qs.filter(category=category)

    if unread_only:
        qs = qs.filter(is_read=False)

    # Ordering: unread first, then by priority, then newest
    qs = qs.order_by(
        "is_read",
        "-priority",
        "-created_at",
    )

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "user/page/notifications.html",
        {
            "page_obj": page_obj,
            "category": category,
            "categories": Notification.Category.choices,
        }
    )
