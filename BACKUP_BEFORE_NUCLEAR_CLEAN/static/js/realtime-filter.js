/**
 * Real-time Filtering System
 * Provides instant search, filter, and sort functionality without page reload.
 */

class RealtimeFilter {
  constructor(options) {
    this.apiUrl = options.apiUrl;
    this.containerSelector = options.containerSelector;
    this.searchInputSelector = options.searchInputSelector;
    this.filterSelector = options.filterSelector;
    this.sortSelector = options.sortSelector;
    this.countSelector = options.countSelector;
    this.statsCallback = options.statsCallback || null;
    
    this.debounceTimer = null;
    this.debounceDelay = 300;
    this.currentParams = {};
    
    this.init();
  }

  init() {
    this.container = document.querySelector(this.containerSelector);
    this.searchInput = document.querySelector(this.searchInputSelector);
    
    if (!this.container) {
      console.warn('RealtimeFilter: Container not found');
      return;
    }

    this.bindEvents();
    this.loadInitialParams();
  }

  loadInitialParams() {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.forEach((value, key) => {
      this.currentParams[key] = value;
    });
  }

  bindEvents() {
    // Search input with debounce
    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.debounce(() => {
          this.currentParams.q = e.target.value;
          this.fetch();
        });
      });

      // Prevent form submission
      const form = this.searchInput.closest('form');
      if (form) {
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          this.currentParams.q = this.searchInput.value;
          this.fetch();
        });
      }
    }

    // Filter buttons/links
    if (this.filterSelector) {
      document.querySelectorAll(this.filterSelector).forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          
          // Get filter params from href or data attributes
          const href = el.getAttribute('href');
          if (href && href !== '#') {
            const params = new URLSearchParams(href.split('?')[1] || '');
            
            // Update current params
            params.forEach((value, key) => {
              this.currentParams[key] = value;
            });
            
            // Remove params not in the new URL (for reset behavior)
            if (!params.has('state')) delete this.currentParams.state;
          }

          // Update active state
          document.querySelectorAll(this.filterSelector).forEach(btn => {
            btn.classList.remove('active');
          });
          el.classList.add('active');

          this.fetch();
        });
      });
    }

    // Sort buttons/links
    if (this.sortSelector) {
      document.querySelectorAll(this.sortSelector).forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          
          const href = el.getAttribute('href');
          if (href) {
            const params = new URLSearchParams(href.split('?')[1] || '');
            this.currentParams.sort = params.get('sort') || '';
          }

          // Update active state
          document.querySelectorAll(this.sortSelector).forEach(btn => {
            btn.classList.remove('active');
          });
          el.classList.add('active');

          this.fetch();
        });
      });
    }

    // Dropdown filters (for users page)
    document.querySelectorAll('.wc-filter-option').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        
        const href = el.getAttribute('href');
        if (href) {
          const params = new URLSearchParams(href.split('?')[1] || '');
          
          // Clear org filters and set new ones
          delete this.currentParams.division;
          delete this.currentParams.section;
          delete this.currentParams.service;
          delete this.currentParams.unit;
          
          params.forEach((value, key) => {
            if (value) this.currentParams[key] = value;
          });
        }

        this.fetch();
        
        // Close dropdown
        const dropdown = el.closest('.wc-filter-menu');
        if (dropdown) dropdown.style.display = 'none';
      });
    });
  }

  debounce(callback) {
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(callback, this.debounceDelay);
  }

  async fetch() {
    // Show loading state
    this.container.classList.add('loading');
    
    // Build query string
    const params = new URLSearchParams();
    Object.entries(this.currentParams).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    try {
      const response = await fetch(`${this.apiUrl}?${params.toString()}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();

      // Update container with new HTML
      this.container.innerHTML = data.html;

      // Update count display
      if (this.countSelector && data.count !== undefined) {
        const countEl = document.querySelector(this.countSelector);
        if (countEl) countEl.textContent = data.count;
      }

      // Call stats callback if provided
      if (this.statsCallback && typeof this.statsCallback === 'function') {
        this.statsCallback(data);
      }

      // Update URL without reload
      this.updateUrl(params);

      // Re-initialize any dynamic elements (dropdowns, etc.)
      this.reinitializeElements();

    } catch (error) {
      console.error('RealtimeFilter fetch error:', error);
      if (window.notify) {
        window.notify('Failed to load data. Please try again.', 'error');
      }
    } finally {
      this.container.classList.remove('loading');
    }
  }

  updateUrl(params) {
    const newUrl = params.toString() 
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;
    
    window.history.replaceState({}, '', newUrl);
  }

  reinitializeElements() {
    // Re-initialize Bootstrap dropdowns
    if (typeof bootstrap !== 'undefined') {
      document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(el => {
        new bootstrap.Dropdown(el);
      });
      
      document.querySelectorAll('[data-bs-toggle="modal"]').forEach(el => {
        // Modal triggers don't need re-initialization
      });
    }
  }
}

// Export for use
window.RealtimeFilter = RealtimeFilter;
