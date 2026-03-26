from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from accounts.models import WorkItem, User


@login_required
def pending_reviews_list(request):
    """
    Display a list of users with their pending review documents.
    Groups pending work items by user.
    """
    # Get all users who have pending work items
    users_with_pending = User.objects.filter(
        work_items__status='done',
        work_items__review_decision='pending'
    ).annotate(
        pending_count=Count('work_items', filter=Q(
            work_items__status='done',
            work_items__review_decision='pending'
        ))
    ).filter(pending_count__gt=0).order_by('-pending_count', 'first_name', 'last_name')
    
    # Get pending work items for each user
    users_data = []
    for user in users_with_pending:
        pending_items = WorkItem.objects.filter(
            owner=user,
            status='done',
            review_decision='pending'
        ).select_related('workcycle').order_by('-submitted_at')
        
        users_data.append({
            'user': user,
            'pending_count': pending_items.count(),
            'pending_items': pending_items
        })
    
    # Get total pending count
    total_pending = WorkItem.objects.filter(
        status='done',
        review_decision='pending'
    ).count()
    
    context = {
        'users_data': users_data,
        'total_pending': total_pending,
    }
    
    return render(request, 'admin/page/pending_reviews.html', context)
