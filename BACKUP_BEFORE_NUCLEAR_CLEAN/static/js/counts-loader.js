/**
 * Asynchronous Counts Loader
 * 
 * Replaces context processors with AJAX calls to improve page load performance.
 * Loads notification, discussion, and email counts after page load.
 */

(function() {
    'use strict';
    
    // Configuration
    const COUNTS_API_URL = '/api/counts/all/';
    const REFRESH_INTERVAL = 30000; // 30 seconds
    let refreshTimer = null;
    
    /**
     * Load all counts from the API
     */
    function loadCounts() {
        fetch(COUNTS_API_URL, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateCountBadges(data);
        })
        .catch(error => {
            console.error('Error loading counts:', error);
        });
    }
    
    /**
     * Update count badges in the UI
     */
    function updateCountBadges(data) {
        // Update discussions count
        updateBadge('discussions-count', data.unread_discussions);
        updateBadge('discussions-badge', data.unread_discussions);
        
        // Update notifications count
        updateBadge('notifications-count', data.unread_notifications);
        updateBadge('notifications-badge', data.unread_notifications);
        
        // Update emails count
        updateBadge('emails-count', data.unread_emails);
        updateBadge('emails-badge', data.unread_emails);
        
        // Update any elements with data-count-type attribute
        document.querySelectorAll('[data-count-type]').forEach(element => {
            const countType = element.getAttribute('data-count-type');
            if (data[countType] !== undefined) {
                updateBadge(element.id, data[countType]);
            }
        });
    }
    
    /**
     * Update a single badge element
     */
    function updateBadge(elementId, count) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        count = parseInt(count) || 0;
        
        if (count > 0) {
            element.textContent = count > 99 ? '99+' : count;
            element.style.display = '';
            element.classList.add('has-unread');
        } else {
            element.textContent = '0';
            element.style.display = 'none';
            element.classList.remove('has-unread');
        }
    }
    
    /**
     * Start auto-refresh
     */
    function startAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        
        refreshTimer = setInterval(loadCounts, REFRESH_INTERVAL);
    }
    
    /**
     * Stop auto-refresh
     */
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }
    
    /**
     * Manually refresh counts (call after actions that change counts)
     */
    function refreshCounts() {
        // Invalidate cache first
        fetch('/api/counts/invalidate/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        })
        .then(() => {
            // Then load fresh counts
            loadCounts();
        })
        .catch(error => {
            console.error('Error invalidating cache:', error);
            // Load counts anyway
            loadCounts();
        });
    }
    
    /**
     * Get CSRF token from cookies
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            loadCounts();
            startAutoRefresh();
        });
    } else {
        loadCounts();
        startAutoRefresh();
    }
    
    // Stop refresh when page is hidden (save resources)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            loadCounts();
            startAutoRefresh();
        }
    });
    
    // Expose refresh function globally
    window.refreshCounts = refreshCounts;
    
})();
