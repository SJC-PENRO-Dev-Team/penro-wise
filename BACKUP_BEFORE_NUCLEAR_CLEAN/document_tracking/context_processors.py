"""
Context processor for document tracking app.
Provides role-based layout selection.
"""

def layout_context(request):
    """
    Determine which base layout to use based on user role.
    
    Returns:
        dict: Context with base_layout path
    """
    if not request.user.is_authenticated:
        # Not authenticated - use user layout as default
        return {'base_layout': 'user/layout/base.html'}
    
    # Check user role
    user_role = getattr(request.user, 'login_role', None)
    
    if user_role == 'admin':
        return {'base_layout': 'admin/layout/base.html'}
    elif user_role == 'user':
        return {'base_layout': 'user/layout/base.html'}
    else:
        # Role not found or invalid - log warning and default to user layout
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"User {request.user.username} (ID: {request.user.id}) has invalid or missing login_role: {user_role}"
        )
        return {'base_layout': 'user/layout/base.html'}
