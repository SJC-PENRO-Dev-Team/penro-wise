/**
 * Unread Count Manager
 * ===================
 * 
 * Handles real-time updates of unread counts for both discussions and notifications
 * without requiring page refresh. Integrates with existing read-receipt logic.
 */

class UnreadCountManager {
  constructor(options = {}) {
    this.options = {
      // API endpoints
      discussionCountEndpoint: '/api/discussions/unread-count/',
      notificationCountEndpoint: '/api/notifications/unread-count/',
      
      // Update intervals (in milliseconds)
      discussionPollInterval: 30000,  // 30 seconds
      notificationPollInterval: 30000, // 30 seconds
      
      // Animation settings
      enableAnimations: true,
      
      // Debug mode
      debug: false,
      
      ...options
    };

    // State tracking
    this.lastCounts = {
      discussions: 0,
      notifications: 0
    };
    
    // Timers
    this.timers = {
      discussions: null,
      notifications: null
    };

    // Initialize
    this.init();
  }

  init() {
    this.log('Initializing UnreadCountManager');
    
    // Get initial counts from DOM
    this.updateInitialCounts();
    
    // Start polling
    this.startPolling();
    
    // Listen for visibility changes to optimize polling
    this.setupVisibilityHandling();
    
    // Listen for custom events from other components
    this.setupEventListeners();
  }

  updateInitialCounts() {
    // Get discussion count from message badge
    const discussionBadge = document.querySelector('[data-unread-type="discussions"]');
    if (discussionBadge) {
      const count = parseInt(discussionBadge.dataset.unreadCount) || 0;
      this.lastCounts.discussions = count;
      this.log('Initial discussion count:', count);
    }

    // Get notification count from notification badge
    const notificationBadge = document.querySelector('[data-unread-type="notifications"]');
    if (notificationBadge) {
      const count = parseInt(notificationBadge.dataset.unreadCount) || 0;
      this.lastCounts.notifications = count;
      this.log('Initial notification count:', count);
    }
  }

  startPolling() {
    // Initial fetch IMMEDIATELY on page load
    this.fetchDiscussionCount();
    this.fetchNotificationCount();
    
    // Start discussion count polling
    if (this.options.discussionPollInterval > 0) {
      this.timers.discussions = setInterval(() => {
        this.fetchDiscussionCount();
      }, this.options.discussionPollInterval);
    }

    // Start notification count polling
    if (this.options.notificationPollInterval > 0) {
      this.timers.notifications = setInterval(() => {
        this.fetchNotificationCount();
      }, this.options.notificationPollInterval);
    }
  }

  stopPolling() {
    if (this.timers.discussions) {
      clearInterval(this.timers.discussions);
      this.timers.discussions = null;
    }
    
    if (this.timers.notifications) {
      clearInterval(this.timers.notifications);
      this.timers.notifications = null;
    }
  }

  setupVisibilityHandling() {
    // Pause polling when page is not visible
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopPolling();
        this.log('Polling paused - page hidden');
      } else {
        this.startPolling();
        this.log('Polling resumed - page visible');
        // Fetch immediately when page becomes visible
        this.fetchDiscussionCount();
        this.fetchNotificationCount();
      }
    });
  }

  setupEventListeners() {
    // Listen for manual refresh events
    document.addEventListener('unread-count:refresh', (e) => {
      const type = e.detail?.type;
      if (type === 'discussions' || !type) {
        this.fetchDiscussionCount();
      }
      if (type === 'notifications' || !type) {
        this.fetchNotificationCount();
      }
    });

    // Listen for count update events (from other components)
    document.addEventListener('unread-count:update', (e) => {
      const { type, count } = e.detail || {};
      if (type && typeof count === 'number') {
        this.updateCount(type, count);
      }
    });

    // Listen for notification panel interactions
    const notificationBell = document.querySelector('[data-notif-toggle]');
    if (notificationBell) {
      notificationBell.addEventListener('click', () => {
        // When notification panel is opened, mark notifications as seen
        setTimeout(() => {
          this.fetchNotificationCount();
        }, 1000);
      });
    }

    // Listen for discussion link clicks
    const discussionLinks = document.querySelectorAll('a[href*="discussions"]');
    discussionLinks.forEach(link => {
      link.addEventListener('click', () => {
        // When discussions page is accessed, refresh count after a delay
        setTimeout(() => {
          this.fetchDiscussionCount();
        }, 2000);
      });
    });
  }

  async fetchDiscussionCount() {
    try {
      const response = await fetch(this.options.discussionCountEndpoint, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'same-origin'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const newCount = data.unread_count || 0;
      this.updateCount('discussions', newCount);

    } catch (error) {
      this.log('Failed to fetch discussion count:', error);
      // Don't show user-facing errors for background polling
    }
  }

  async fetchNotificationCount() {
    try {
      this.log('Fetching notification count from:', this.options.notificationCountEndpoint);
      
      const response = await fetch(this.options.notificationCountEndpoint, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'same-origin'
      });

      this.log('Notification count response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      this.log('Notification count data:', data);
      
      const newCount = data.unread_count || 0;
      this.log('Updating notification count to:', newCount);
      this.updateCount('notifications', newCount);

    } catch (error) {
      this.log('Failed to fetch notification count:', error);
      console.error('[UnreadCountManager] Notification count fetch error:', error);
      // Don't show user-facing errors for background polling
    }
  }

  updateCount(type, newCount) {
    if (typeof newCount !== 'number') return;

    const oldCount = this.lastCounts[type];
    if (oldCount === newCount) return; // No change

    this.lastCounts[type] = newCount;
    this.log(`${type} count updated: ${oldCount} → ${newCount}`);

    // Update DOM
    const badge = document.querySelector(`[data-unread-type="${type}"]`);
    if (badge) {
      this.updateBadge(badge, newCount, oldCount);
    }

    // Dispatch custom event
    document.dispatchEvent(new CustomEvent('unread-count:changed', {
      detail: { type, oldCount, newCount }
    }));
  }

  updateBadge(badge, newCount, oldCount) {
    // Update data attribute
    badge.dataset.unreadCount = newCount;

    // Update display text
    const displayText = newCount > 99 ? '99+' : newCount.toString();
    badge.textContent = displayText;

    // Update visibility
    if (newCount > 0) {
      badge.style.display = 'flex';
      badge.setAttribute('aria-label', `${newCount} unread ${badge.dataset.unreadType === 'discussions' ? 'message' + (newCount !== 1 ? 's' : '') : 'notification' + (newCount !== 1 ? 's' : '')}`);
    } else {
      badge.style.display = 'none';
      badge.setAttribute('aria-label', `No unread ${badge.dataset.unreadType === 'discussions' ? 'messages' : 'notifications'}`);
    }

    // Add animations if enabled
    if (this.options.enableAnimations) {
      this.animateBadge(badge, newCount, oldCount);
    }
  }

  animateBadge(badge, newCount, oldCount) {
    // Remove existing animation classes
    badge.classList.remove('unread-count-increment', 'unread-count-decrement', 'unread-count-update');

    // Force reflow
    void badge.offsetWidth;

    if (newCount > oldCount) {
      // Count increased
      badge.classList.add('unread-count-increment');
      this.log(`${badge.dataset.unreadType} count increased`, { oldCount, newCount });
    } else if (newCount < oldCount) {
      // Count decreased
      badge.classList.add('unread-count-decrement');
      this.log(`${badge.dataset.unreadType} count decreased`, { oldCount, newCount });
    } else {
      // General update
      badge.classList.add('unread-count-update');
    }

    // Add new-unread class for shine effect
    if (newCount > oldCount && newCount > 0) {
      badge.classList.add('new-unread');
      setTimeout(() => {
        badge.classList.remove('new-unread');
      }, 500);
    }

    // Remove animation classes after animation completes
    setTimeout(() => {
      badge.classList.remove('unread-count-increment', 'unread-count-decrement', 'unread-count-update');
    }, 1000);
  }

  // Public methods for manual control
  refreshCounts(type = null) {
    if (type === 'discussions') {
      this.fetchDiscussionCount();
    } else if (type === 'notifications') {
      this.fetchNotificationCount();
    } else {
      this.fetchDiscussionCount();
      this.fetchNotificationCount();
    }
  }

  getCurrentCounts() {
    return { ...this.lastCounts };
  }

  destroy() {
    this.log('Destroying UnreadCountManager');
    this.stopPolling();
    
    // Remove event listeners
    document.removeEventListener('unread-count:refresh', this.handleRefreshEvent);
    document.removeEventListener('unread-count:update', this.handleUpdateEvent);
  }

  log(...args) {
    if (this.options.debug) {
      console.log('[UnreadCountManager]', ...args);
    }
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize if we have unread count elements
  const hasUnreadElements = document.querySelector('[data-unread-type]');
  
  if (hasUnreadElements) {
    window.unreadCountManager = new UnreadCountManager({
      debug: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    });
    
    // Expose global methods for manual control
    window.refreshUnreadCounts = (type) => {
      window.unreadCountManager.refreshCounts(type);
    };
    
    window.getCurrentUnreadCounts = () => {
      return window.unreadCountManager.getCurrentCounts();
    };
  }
});

// Export for manual initialization
window.UnreadCountManager = UnreadCountManager;
