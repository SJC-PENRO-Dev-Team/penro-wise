/**
 * Notification Panel JavaScript
 * =============================
 * 
 * Facebook-style floating notification panel.
 * Handles fetching, displaying, and marking notifications as read.
 * Includes real-time toast notifications for new notifications.
 */

class NotificationPanel {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      listEndpoint: '/api/notifications/',
      countEndpoint: '/api/notifications/unread-count/',
      markReadEndpoint: '/api/notifications/{id}/read/',
      markAllReadEndpoint: '/api/notifications/mark-all-read/',
      viewAllUrl: '/notifications/',
      limit: 10,
      pollInterval: 30000, // Poll every 30 seconds for new notifications
      enableToasts: true,  // Show toast notifications for new items
      ...options
    };

    // DOM elements
    this.bell = container.querySelector('[data-notif-toggle]');
    this.badge = container.querySelector('[data-notif-badge]');
    this.panel = container.querySelector('[data-notif-dropdown]');
    this.list = container.querySelector('[data-notif-list]');
    this.markAllBtn = container.querySelector('[data-mark-all-read]');
    this.footer = container.querySelector('[data-notif-footer]');

    // State
    this.isOpen = false;
    this.isLoading = false;
    this.page = 1;
    this.hasMore = false;
    this.notifications = [];
    this.lastKnownCount = parseInt(this.badge?.dataset.count || '0');
    this.seenNotificationIds = new Set();
    this.pollTimer = null;

    // Category icon mapping
    this.categoryIcons = {
      reminder: { icon: 'fa-clock', class: 'notif-icon-reminder' },
      status: { icon: 'fa-check-circle', class: 'notif-icon-status' },
      review: { icon: 'fa-clipboard-check', class: 'notif-icon-review' },
      assignment: { icon: 'fa-user-plus', class: 'notif-icon-assignment' },
      message: { icon: 'fa-comment', class: 'notif-icon-message' },
      system: { icon: 'fa-cog', class: 'notif-icon-system' }
    };

    this.init();
  }

  init() {
    if (!this.bell || !this.panel) {
      console.warn('NotificationPanel: Required elements not found');
      return;
    }

    // Bind events
    this.bell.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (this.isOpen && !this.container.contains(e.target)) {
        this.close();
      }
    });
    
    // Close on backdrop click
    const backdrop = document.querySelector('[data-notif-backdrop]');
    if (backdrop) {
      backdrop.addEventListener('click', () => {
        this.close();
      });
    }

    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
        this.bell.focus();
      }
    });

    // Mark all as read
    if (this.markAllBtn) {
      this.markAllBtn.addEventListener('click', () => this.markAllAsRead());
    }

    // Scroll for load more
    if (this.list) {
      this.list.addEventListener('scroll', () => this.handleScroll());
    }

    // Keyboard navigation on bell
    this.bell.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggle();
      }
    });

    // Start polling for new notifications
    this.startPolling();
    
    // Initial fetch of notification IDs to track what's "seen"
    this.initializeSeenNotifications();
  }

  async initializeSeenNotifications() {
    try {
      const response = await fetch(`${this.options.listEndpoint}?limit=20`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (response.ok) {
        const data = await response.json();
        data.notifications.forEach(n => this.seenNotificationIds.add(n.id));
      }
    } catch (err) {
      // Silently fail - not critical
    }
  }

  startPolling() {
    if (this.options.pollInterval > 0) {
      this.pollTimer = setInterval(() => this.checkForNewNotifications(), this.options.pollInterval);
    }
  }

  stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  async checkForNewNotifications() {
    try {
      const response = await fetch(this.options.countEndpoint, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });

      if (!response.ok) return;

      const data = await response.json();
      const newCount = data.unread_count;

      // If count increased, fetch new notifications and show toasts
      if (newCount > this.lastKnownCount && this.options.enableToasts) {
        await this.fetchAndShowNewNotifications();
      }

      this.updateBadge(newCount);
      this.lastKnownCount = newCount;

    } catch (error) {
      // Silently fail - network issues shouldn't break the UI
    }
  }

  async fetchAndShowNewNotifications() {
    try {
      const response = await fetch(`${this.options.listEndpoint}?limit=5&unread_only=true`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });

      if (!response.ok) return;

      const data = await response.json();
      
      // Show toast for each new notification we haven't seen
      for (const notif of data.notifications) {
        if (!this.seenNotificationIds.has(notif.id)) {
          this.showNotificationToast(notif);
          this.seenNotificationIds.add(notif.id);
        }
      }

    } catch (error) {
      // Silently fail
    }
  }

  showNotificationToast(notif) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('notif-toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'notif-toast-container';
      toastContainer.className = 'notif-toast-container';
      document.body.appendChild(toastContainer);
    }

    const iconConfig = this.categoryIcons[notif.category] || this.categoryIcons.system;
    
    const toast = document.createElement('div');
    toast.className = `notif-toast notif-toast-${notif.priority || 'info'}`;
    toast.innerHTML = `
      <div class="notif-toast-icon ${iconConfig.class}">
        <i class="fas ${iconConfig.icon}"></i>
      </div>
      <div class="notif-toast-content">
        <div class="notif-toast-title">${this.escapeHtml(notif.title)}</div>
        <div class="notif-toast-message">${this.escapeHtml(notif.message)}</div>
      </div>
      <button class="notif-toast-close" aria-label="Close">
        <i class="fas fa-times"></i>
      </button>
    `;

    // Click to navigate
    toast.addEventListener('click', (e) => {
      if (!e.target.closest('.notif-toast-close')) {
        if (notif.action_url) {
          // Always navigate to the URL, never open modal
          window.location.href = notif.action_url;
        }
        this.dismissToast(toast);
      }
    });

    // Close button
    toast.querySelector('.notif-toast-close').addEventListener('click', (e) => {
      e.stopPropagation();
      this.dismissToast(toast);
    });

    toastContainer.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto dismiss after 8 seconds
    setTimeout(() => this.dismissToast(toast), 8000);
  }

  dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.remove('show');
    toast.classList.add('hide');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.isOpen = true;
    this.panel.classList.add('show');
    this.bell.classList.add('active');
    this.bell.setAttribute('aria-expanded', 'true');
    
    // Close documents panel if open (admin)
    const docsPanel = document.querySelector('[data-docs-content]');
    const docsBackdrop = document.querySelector('[data-docs-backdrop]');
    if (docsPanel) {
      docsPanel.classList.remove('show');
    }
    if (docsBackdrop) {
      docsBackdrop.classList.remove('show');
    }
    
    // Close user menu if open
    const userMenu = document.querySelector('[data-user-menu]');
    const userBackdrop = document.querySelector('[data-user-backdrop]');
    if (userMenu) {
      userMenu.classList.remove('open');
    }
    if (userBackdrop) {
      userBackdrop.classList.remove('show');
    }
    
    // Close mobile nav if open (user)
    const nav = document.querySelector('[data-nav]');
    const navBackdrop = document.querySelector('[data-nav-backdrop]');
    if (nav) {
      nav.classList.remove('show');
    }
    if (navBackdrop) {
      navBackdrop.classList.remove('show');
    }
    
    // Show backdrop
    const backdrop = document.querySelector('[data-notif-backdrop]');
    if (backdrop) {
      backdrop.classList.add('show');
    }

    // Reset and fetch
    this.page = 1;
    this.notifications = [];
    this.fetchNotifications();
  }

  close() {
    this.isOpen = false;
    this.panel.classList.remove('show');
    this.bell.classList.remove('active');
    this.bell.setAttribute('aria-expanded', 'false');
    
    // Hide backdrop
    const backdrop = document.querySelector('[data-notif-backdrop]');
    if (backdrop) {
      backdrop.classList.remove('show');
    }
  }

  async fetchNotifications(append = false) {
    if (this.isLoading) return;

    this.isLoading = true;
    
    if (!append) {
      this.showLoading();
    }

    try {
      const url = `${this.options.listEndpoint}?page=${this.page}&limit=${this.options.limit}`;
      const response = await fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      if (append) {
        this.notifications = [...this.notifications, ...data.notifications];
      } else {
        this.notifications = data.notifications;
      }

      // Track seen notifications
      data.notifications.forEach(n => this.seenNotificationIds.add(n.id));

      this.hasMore = data.has_more;
      this.updateBadge(data.unread_count);
      this.lastKnownCount = data.unread_count;
      this.renderNotifications();

    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      this.showError();
    } finally {
      this.isLoading = false;
    }
  }

  async fetchUnreadCount() {
    try {
      const response = await fetch(this.options.countEndpoint, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (response.ok) {
        const data = await response.json();
        this.updateBadge(data.unread_count);
        this.lastKnownCount = data.unread_count;
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  }

  async markAsRead(id, element) {
    try {
      const url = this.options.markReadEndpoint.replace('{id}', id);
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': this.getCSRFToken()
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update UI
        if (element) {
          element.classList.remove('notif-unread');
        }
        
        // Update notification in array
        const notif = this.notifications.find(n => n.id === id);
        if (notif) {
          notif.is_read = true;
        }

        this.updateBadge(data.unread_count);
        this.lastKnownCount = data.unread_count;
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }

  async markAllAsRead() {
    if (this.markAllBtn) {
      this.markAllBtn.disabled = true;
      this.markAllBtn.textContent = 'Marking...';
    }

    try {
      const response = await fetch(this.options.markAllReadEndpoint, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': this.getCSRFToken()
        }
      });

      if (response.ok) {
        const data = await response.json();

        // Update all notifications in array
        this.notifications.forEach(n => n.is_read = true);

        // Update UI
        this.list.querySelectorAll('.notif-unread').forEach(el => {
          el.classList.remove('notif-unread');
        });

        this.updateBadge(data.unread_count);
        this.lastKnownCount = data.unread_count;
      }
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    } finally {
      if (this.markAllBtn) {
        this.markAllBtn.disabled = false;
        this.markAllBtn.textContent = 'Mark all as read';
      }
    }
  }

  renderNotifications() {
    if (!this.list) return;

    if (this.notifications.length === 0) {
      this.showEmpty();
      return;
    }

    // Group by time
    const groups = this.groupByTime(this.notifications);
    
    let html = '';
    
    for (const [groupName, items] of Object.entries(groups)) {
      if (items.length === 0) continue;
      
      html += `<div class="notif-group-header">${groupName}</div>`;
      
      for (const notif of items) {
        html += this.renderNotificationItem(notif);
      }
    }

    // Add load more button if needed
    if (this.hasMore) {
      html += `
        <div class="notif-load-more">
          <button class="notif-load-more-btn" data-load-more>Load more</button>
        </div>
      `;
    }

    this.list.innerHTML = html;

    // Bind click events
    this.list.querySelectorAll('.notif-item').forEach(item => {
      item.addEventListener('click', (e) => this.handleItemClick(e, item));
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          this.handleItemClick(e, item);
        }
      });
    });

    // Bind load more
    const loadMoreBtn = this.list.querySelector('[data-load-more]');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => this.loadMore());
    }
  }

  renderNotificationItem(notif) {
    const iconConfig = this.categoryIcons[notif.category] || this.categoryIcons.system;
    const unreadClass = notif.is_read ? '' : 'notif-unread';
    const timeAgo = this.formatTimeAgo(notif.created_at);
    const hasAction = notif.action_url || notif.work_item_id || notif.workcycle_id;

    return `
      <div class="notif-item ${unreadClass} ${hasAction ? 'notif-clickable' : ''}" 
           data-notif-id="${notif.id}" 
           data-action-url="${notif.action_url || ''}"
           data-category="${notif.category || ''}"
           tabindex="0"
           role="menuitem">
        <div class="notif-icon ${iconConfig.class}">
          <i class="fas ${iconConfig.icon}"></i>
        </div>
        <div class="notif-content">
          <div class="notif-title">${this.escapeHtml(notif.title)}</div>
          <div class="notif-message">${this.escapeHtml(notif.message)}</div>
          <div class="notif-meta">
            <span class="notif-time">${timeAgo}</span>
            ${hasAction ? '<span class="notif-action-hint"><i class="fas fa-arrow-right"></i></span>' : ''}
          </div>
        </div>
      </div>
    `;
  }

  handleItemClick(e, item) {
    // Prevent any default actions and stop propagation
    e.preventDefault();
    e.stopPropagation();
    
    const id = parseInt(item.dataset.notifId);
    const actionUrl = item.dataset.actionUrl;

    // Mark as read
    if (item.classList.contains('notif-unread')) {
      this.markAsRead(id, item);
    }

    // Navigate if URL exists - always navigate, never open modal
    if (actionUrl) {
      window.location.href = actionUrl;
    }
  }

  loadMore() {
    this.page++;
    this.fetchNotifications(true);
  }

  handleScroll() {
    if (!this.hasMore || this.isLoading) return;

    const { scrollTop, scrollHeight, clientHeight } = this.list;
    
    if (scrollTop + clientHeight >= scrollHeight - 50) {
      this.loadMore();
    }
  }

  groupByTime(notifications) {
    const groups = {
      'Today': [],
      'Yesterday': [],
      'Earlier this week': [],
      'Earlier': []
    };

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    for (const notif of notifications) {
      const date = new Date(notif.created_at);
      
      if (date >= today) {
        groups['Today'].push(notif);
      } else if (date >= yesterday) {
        groups['Yesterday'].push(notif);
      } else if (date >= weekAgo) {
        groups['Earlier this week'].push(notif);
      } else {
        groups['Earlier'].push(notif);
      }
    }

    return groups;
  }

  formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    } else if (diffDays === 1) {
      return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  }

  updateBadge(count) {
    if (!this.badge) return;

    if (count > 0) {
      this.badge.textContent = count > 9 ? '9+' : count;
      this.badge.style.display = 'flex';
      this.badge.setAttribute('data-count', count);
    } else {
      this.badge.style.display = 'none';
      this.badge.setAttribute('data-count', '0');
    }

    // Update ARIA
    this.bell.setAttribute('aria-label', `Notifications (${count} unread)`);
  }

  showLoading() {
    if (!this.list) return;
    
    this.list.innerHTML = `
      <div class="notif-loading">
        <div class="notif-spinner"></div>
      </div>
    `;
  }

  showEmpty() {
    if (!this.list) return;
    
    this.list.innerHTML = `
      <div class="notif-empty">
        <div class="notif-empty-icon">
          <i class="fas fa-bell-slash"></i>
        </div>
        <div class="notif-empty-text">No notifications yet</div>
      </div>
    `;
  }

  showError() {
    if (!this.list) return;
    
    this.list.innerHTML = `
      <div class="notif-empty">
        <div class="notif-empty-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="notif-empty-text">Failed to load notifications</div>
      </div>
    `;
  }

  getCSRFToken() {
    // Try to get from cookie
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value;
      }
    }
    
    // Try to get from meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
      return meta.getAttribute('content');
    }

    // Try to get from hidden input
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) {
      return input.value;
    }

    return '';
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const containers = document.querySelectorAll('[data-notif-panel]');
  
  containers.forEach(container => {
    const viewAllUrl = container.dataset.viewAllUrl || '/notifications/';
    
    new NotificationPanel(container, {
      viewAllUrl: viewAllUrl
    });
  });
});

// Export for manual initialization
window.NotificationPanel = NotificationPanel;
