"""
Update all_files_uploaded.html with new toolbar and routed documents filtering
"""

# Read current template
with open('templates/admin/page/all_files_uploaded.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the toolbar section
old_toolbar = '''    <!-- Toolbar -->
    <div class="fm-toolbar">
      <nav class="fm-breadcrumb">
        <span class="fm-crumb current">
          <i class="fas fa-check-circle"></i>
          All Accepted Files
        </span>
      </nav>
      
      <div class="fm-toolbar-actions">
        <div class="fm-view-toggle d-none d-md-flex">
          <button class="fm-view-btn active" data-view="grid" title="Grid view">
            <i class="fas fa-th-large"></i>
          </button>
          <button class="fm-view-btn" data-view="list" title="List view">
            <i class="fas fa-list"></i>
          </button>
        </div>
        
        <div class="fm-toolbar-divider"></div>
        
        <button class="fm-action-btn" onclick="refreshView()" title="Refresh">
          <i class="fas fa-sync-alt"></i>
        </button>
      </div>
    </div>'''

new_toolbar = '''    <!-- Navigation Tabs Toolbar -->
    <div class="fm-toolbar" style="flex-direction: column; align-items: stretch; padding: 0;">
      <!-- Tab Navigation -->
      <div class="fm-tabs" style="display: flex; border-bottom: 2px solid #e2e8f0; background: #f8fafc;">
        <button class="fm-tab active" data-tab="routed" onclick="switchTab('routed')" style="flex: 1; padding: 16px 24px; border: none; background: none; font-size: 0.95rem; font-weight: 600; color: #64748b; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s;">
          <i class="fas fa-route" style="margin-right: 8px;"></i>
          Routed Documents/Assets
        </button>
        <button class="fm-tab" data-tab="workstate" onclick="switchTab('workstate')" style="flex: 1; padding: 16px 24px; border: none; background: none; font-size: 0.95rem; font-weight: 600; color: #64748b; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s;">
          <i class="fas fa-tasks" style="margin-right: 8px;"></i>
          Workstate Assets
        </button>
      </div>
      
      <!-- Filter Bar (Routed Documents) -->
      <div id="routedFilters" class="fm-filter-bar" style="display: flex; align-items: center; gap: 12px; padding: 12px 20px; background: white; border-bottom: 1px solid #e2e8f0;">
        <span style="font-size: 0.875rem; font-weight: 600; color: #64748b;">Filter by:</span>
        
        <div class="filter-dropdown-container" style="position: relative;">
          <button class="fm-filter-btn" onclick="toggleFilterDropdown('submission')" style="padding: 8px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: white; font-size: 0.875rem; font-weight: 500; color: #475569; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-file-alt"></i>
            Name of Submission
            <i class="fas fa-chevron-down" style="font-size: 0.75rem;"></i>
          </button>
          <div id="submissionDropdown" class="filter-dropdown" style="display: none; position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 300px; max-width: 400px; z-index: 1000;">
            <div style="padding: 12px;">
              <input type="text" id="submissionSearch" placeholder="Search submissions..." style="width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.875rem;" oninput="searchFilter('submission', this.value)">
            </div>
            <div id="submissionResults" class="filter-results" style="max-height: 300px; overflow-y: auto;">
              <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 0.875rem;">
                Type to search...
              </div>
            </div>
          </div>
        </div>
        
        <div class="filter-dropdown-container" style="position: relative;">
          <button class="fm-filter-btn" onclick="toggleFilterDropdown('tracking')" style="padding: 8px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: white; font-size: 0.875rem; font-weight: 500; color: #475569; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-hashtag"></i>
            Tracking Number
            <i class="fas fa-chevron-down" style="font-size: 0.75rem;"></i>
          </button>
          <div id="trackingDropdown" class="filter-dropdown" style="display: none; position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 300px; max-width: 400px; z-index: 1000;">
            <div style="padding: 12px;">
              <input type="text" id="trackingSearch" placeholder="Search tracking numbers..." style="width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.875rem;" oninput="searchFilter('tracking', this.value)">
            </div>
            <div id="trackingResults" class="filter-results" style="max-height: 300px; overflow-y: auto;">
              <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 0.875rem;">
                Type to search...
              </div>
            </div>
          </div>
        </div>
        
        <div class="filter-dropdown-container" style="position: relative;">
          <button class="fm-filter-btn" onclick="toggleFilterDropdown('file')" style="padding: 8px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: white; font-size: 0.875rem; font-weight: 500; color: #475569; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-paperclip"></i>
            File/Image/Asset Name
            <i class="fas fa-chevron-down" style="font-size: 0.75rem;"></i>
          </button>
          <div id="fileDropdown" class="filter-dropdown" style="display: none; position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 300px; max-width: 400px; z-index: 1000;">
            <div style="padding: 12px;">
              <input type="text" id="fileSearch" placeholder="Search file names..." style="width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.875rem;" oninput="searchFilter('file', this.value)">
            </div>
            <div id="fileResults" class="filter-results" style="max-height: 300px; overflow-y: auto;">
              <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 0.875rem;">
                Type to search...
              </div>
            </div>
          </div>
        </div>
        
        <div style="flex: 1;"></div>
        
        <div class="fm-view-toggle d-none d-md-flex" style="display: flex; gap: 4px;">
          <button class="fm-view-btn active" data-view="grid" title="Grid view" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; cursor: pointer;">
            <i class="fas fa-th-large"></i>
          </button>
          <button class="fm-view-btn" data-view="list" title="List view" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; cursor: pointer;">
            <i class="fas fa-list"></i>
          </button>
        </div>
        
        <button class="fm-action-btn" onclick="refreshView()" title="Refresh" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; cursor: pointer;">
          <i class="fas fa-sync-alt"></i>
        </button>
      </div>
      
      <!-- Workstate Placeholder -->
      <div id="workstateFilters" class="fm-filter-bar" style="display: none; padding: 20px; background: #f8fafc; text-align: center; color: #64748b;">
        <i class="fas fa-info-circle" style="font-size: 1.5rem; margin-bottom: 12px; color: #94a3b8;"></i>
        <p style="margin: 0; font-size: 0.95rem;">Workstate Assets view coming soon...</p>
      </div>
    </div>'''

# Replace
content = content.replace(old_toolbar, new_toolbar)

# Write back
with open('templates/admin/page/all_files_uploaded.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Updated toolbar with navigation tabs")
print("✓ Added filter dropdowns with real-time search")
print("✓ Added Workstate Assets placeholder")
print("✓ Ready to add JavaScript!")
