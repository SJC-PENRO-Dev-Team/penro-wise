"""
Status Workflow Management for Document Tracking System

This module enforces strict status transition rules based on the workflow diagram.
NO status can be skipped or jumped - all transitions must follow the defined paths.
"""


class StatusWorkflow:
    """
    Manages status transitions and workflow logic.
    
    Workflow Structure:
    1. Received/Submitted (pending_tracking) → Initial state
    2A. Incomplete (returned_to_sender) → Request corrections
    2B. For Routing (received) → Ready to assign
    3. Under Review (under_review) → Section evaluation
    4A. For Compliance (for_compliance) → Needs revision
    4B. Approved (approved) → Final approval (files stored in File Manager)
    4C. Rejected (rejected) → Final rejection
    
    NOTE: 'archived' status removed - approved/rejected are now terminal states
    """
    
    # Define valid transitions from each status
    TRANSITIONS = {
        'pending_tracking': ['received', 'returned_to_sender'],  # Initial review
        'returned_to_sender': ['under_review'],  # After corrections
        'received': ['under_review'],  # After routing
        'under_review': ['for_compliance', 'approved', 'rejected'],  # Section decision
        'for_compliance': ['under_review'],  # After compliance submission
        'approved': [],  # Terminal state (files stored in File Manager)
        'rejected': [],  # Terminal state
    }
    
    # Status levels for progress indicator
    STATUS_LEVELS = {
        'pending_tracking': {'level': 1, 'label': 'Received/Submitted', 'color': 'blue'},
        'returned_to_sender': {'level': 2, 'label': 'Incomplete', 'color': 'orange', 'branch': 'correction'},
        'received': {'level': 2, 'label': 'For Routing', 'color': 'yellow', 'branch': 'main'},
        'under_review': {'level': 3, 'label': 'Under Review', 'color': 'blue'},
        'for_compliance': {'level': 4, 'label': 'For Compliance', 'color': 'orange', 'branch': 'revision'},
        'approved': {'level': 5, 'label': 'Approved', 'color': 'green', 'branch': 'approved'},
        'rejected': {'level': 5, 'label': 'Rejected', 'color': 'red', 'branch': 'rejected'},
    }
    
    # Human-readable status descriptions
    STATUS_DESCRIPTIONS = {
        'pending_tracking': 'Document submitted and awaiting initial review',
        'returned_to_sender': 'Document incomplete - corrections requested',
        'received': 'Document complete and ready for section assignment',
        'under_review': 'Document under evaluation by assigned section',
        'for_compliance': 'Document requires revisions from applicant',
        'approved': 'Document approved - files stored in File Manager',
        'rejected': 'Document rejected - no further action',
    }
    
    @classmethod
    def get_next_statuses(cls, current_status):
        """
        Get list of valid next statuses from current status.
        
        Args:
            current_status: Current status code
            
        Returns:
            List of valid next status codes
        """
        return cls.TRANSITIONS.get(current_status, [])
    
    @classmethod
    def can_transition(cls, from_status, to_status):
        """
        Check if transition from one status to another is valid.
        
        Args:
            from_status: Current status code
            to_status: Target status code
            
        Returns:
            Boolean indicating if transition is allowed
        """
        valid_transitions = cls.TRANSITIONS.get(from_status, [])
        return to_status in valid_transitions
    
    @classmethod
    def get_status_info(cls, status):
        """
        Get detailed information about a status.
        
        Args:
            status: Status code
            
        Returns:
            Dictionary with level, label, color, and optional branch
        """
        return cls.STATUS_LEVELS.get(status, {})
    
    @classmethod
    def get_status_description(cls, status):
        """
        Get human-readable description of a status.
        
        Args:
            status: Status code
            
        Returns:
            String description
        """
        return cls.STATUS_DESCRIPTIONS.get(status, '')
    
    @classmethod
    def get_workflow_path(cls, submission):
        """
        Get the complete workflow path taken by a submission.
        
        Args:
            submission: Submission instance
            
        Returns:
            List of status codes in order
        """
        # Get logbook entries ordered by timestamp
        logs = submission.logs.order_by('timestamp')
        
        # Extract unique statuses in order
        path = []
        for log in logs:
            if log.new_status and log.new_status not in path:
                path.append(log.new_status)
        
        # Add current status if not in path
        if submission.status not in path:
            path.append(submission.status)
        
        return path
    
    @classmethod
    def get_progress_percentage(cls, status):
        """
        Calculate progress percentage based on status level.
        
        Args:
            status: Status code
            
        Returns:
            Integer percentage (0-100)
        """
        info = cls.get_status_info(status)
        level = info.get('level', 1)
        
        # Terminal states are 100%
        if status in ['approved', 'rejected']:
            return 100
        
        # Calculate based on level (1-5)
        return int((level / 5) * 100)
    
    @classmethod
    def is_terminal_status(cls, status):
        """
        Check if status is terminal (no further transitions).
        
        Args:
            status: Status code
            
        Returns:
            Boolean
        """
        return len(cls.TRANSITIONS.get(status, [])) == 0
    
    @classmethod
    def get_status_actions(cls, current_status):
        """
        Get available actions for current status with labels.
        
        Args:
            current_status: Current status code
            
        Returns:
            List of tuples (status_code, label, description, color)
        """
        next_statuses = cls.get_next_statuses(current_status)
        actions = []
        
        for status in next_statuses:
            info = cls.get_status_info(status)
            actions.append({
                'code': status,
                'label': info.get('label', status),
                'description': cls.get_status_description(status),
                'color': info.get('color', 'gray'),
            })
        
        return actions
    
    @classmethod
    def can_reset_to_start(cls, current_status):
        """
        Check if submission can be reset to initial state.
        Available from Step 2 onwards (not just archived).
        
        Args:
            current_status: Current status code
            
        Returns:
            Boolean
        """
        # Allow reset from any status except pending_tracking (Step 1)
        return current_status != 'pending_tracking'
    
    @classmethod
    def get_previous_status(cls, current_status, workflow_path):
        """
        Get the previous status in the workflow path for undo functionality.
        
        Args:
            current_status: Current status code
            workflow_path: List of statuses in order
            
        Returns:
            Previous status code or None
        """
        if not workflow_path or len(workflow_path) < 2:
            return None
        
        # Find current status in path
        try:
            current_index = workflow_path.index(current_status)
            if current_index > 0:
                return workflow_path[current_index - 1]
        except ValueError:
            pass
        
        return None
