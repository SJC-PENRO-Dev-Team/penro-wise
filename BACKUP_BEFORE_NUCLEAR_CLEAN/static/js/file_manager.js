/**
 * File Manager JavaScript
 * Handles selection, actions, view toggle, breadcrumb overflow, and mobile responsiveness
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get URLs from FM object (defined in template)
  const urls = window.FM?.urls || {};
  
  // State
  let selectedItems = new Set();
  let clipboardItems = [];
  let clipboardAction = null; // 'cut' or 'copy'
  
  // Elements
  const selectionActions = document.getElementById('selectionActions');
  const normalActions = document.getElementById('normalActions');
  const selectionCount = document.getElementById('selectionCount');
  const checkboxes = document.querySelectorAll('.fm-checkbox');
  const items = document.querySelectorAll('.fm-item');
  
  // Modals
  const createFolderModalEl = document.getElementById('createFolderModal');
  
  let createFolderModal;
  if (createFolderModalEl) {
    createFolderModal = new bootstrap.Modal(createFolderModalEl);
  }
  
  // Get CSRF token
  function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
           '';
  }
  
  // ==========================================
  // BREADCRUMB OVERFLOW HANDLING
  // ==========================================
  function handleBreadcrumbOverflow() {
    const breadcrumb = document.getElementById('breadcrumbNav');
    if (!breadcrumb) return;
    
    const crumbs = Array.from(breadcrumb.querySelectorAll('.fm-crumb:not(.current)'));
    const separators = Array.from(breadcrumb.querySelectorAll('.fm-crumb-sep'));
    
    // Reset visibility
    crumbs.forEach(c => c.style.display = '');
    separators.forEach(s => s.style.display = '');
  }
  
  // ==========================================
  // MOBILE BREADCRUMB - Simple dropdown toggle
  // ==========================================
  const breadcrumbDropdownBtn = document.getElementById('breadcrumbDropdown');
  console.log('Breadcrumb dropdown button:', breadcrumbDropdownBtn);
  
  if (breadcrumbDropdownBtn) {
    const dropdownMenu = breadcrumbDropdownBtn.nextElementSibling;
    console.log('Dropdown menu:', dropdownMenu);
    
    breadcrumbDropdownBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('Ellipsis clicked!');
      console.log('Current classes:', dropdownMenu.className);
      
      // Toggle show class
      const isOpen = dropdownMenu.classList.contains('show');
      console.log('Is currently open?', isOpen);
      
      if (isOpen) {
        console.log('Closing dropdown');
        dropdownMenu.classList.remove('show');
        breadcrumbDropdownBtn.classList.remove('show');
      } else {
        console.log('Opening dropdown');
        dropdownMenu.classList.add('show');
        breadcrumbDropdownBtn.classList.add('show');
      }
      
      console.log('After toggle:', dropdownMenu.className);
    });
    
    // Close when clicking outside
    document.addEventListener('click', function(e) {
      if (!breadcrumbDropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove('show');
        breadcrumbDropdownBtn.classList.remove('show');
      }
    });
  } else {
    console.log('Breadcrumb dropdown button NOT FOUND');
  }
  
  // Run on load and resize
  handleBreadcrumbOverflow();
  window.addEventListener('resize', handleBreadcrumbOverflow);
  const mobileNavBtn2026 = document.getElementById('mobileNavEllipsisBtn2026');
  const mobileNavPanel2026 = document.getElementById('mobileNavDropPanel2026');
  const mobileNavClose2026 = document.getElementById('mobileNavCloseBtn2026');
  const mobileNavBackdrop2026 = document.getElementById('mobileNavBackdrop2026');
  
  console.log('=== MOBILE NAV DEBUG ===');
  console.log('Button element:', mobileNavBtn2026);
  console.log('Panel element:', mobileNavPanel2026);
  console.log('Close button:', mobileNavClose2026);
  console.log('Backdrop element:', mobileNavBackdrop2026);
  
  if (mobileNavPanel2026) {
    const panelStyle = window.getComputedStyle(mobileNavPanel2026);
    console.log('Panel position:', {
      position: panelStyle.position,
      bottom: panelStyle.bottom,
      left: panelStyle.left,
      right: panelStyle.right,
      zIndex: panelStyle.zIndex,
      transform: panelStyle.transform,
      visibility: panelStyle.visibility,
      opacity: panelStyle.opacity,
      display: panelStyle.display
    });
  }
  
  // Only set up event listeners if button exists (breadcrumb length > 3)
  if (mobileNavBtn2026 && mobileNavPanel2026) {
    console.log('✓ Setting up mobile breadcrumb menu...');
    
    // TEST: Add test-visible class temporarily
    setTimeout(() => {
      console.log('TEST: Adding test-visible class to panel');
      mobileNavPanel2026.classList.add('test-visible');
      setTimeout(() => {
        console.log('TEST: Removing test-visible class');
        mobileNavPanel2026.classList.remove('test-visible');
      }, 3000);
    }, 1000);
    
    // Toggle panel
    mobileNavBtn2026.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('🔵 Mobile nav button CLICKED!');
      console.log('Panel before toggle:', mobileNavPanel2026.className);
      
      const isActive = mobileNavPanel2026.classList.contains('active-panel-2026');
      
      if (isActive) {
        // Close
        mobileNavPanel2026.classList.remove('active-panel-2026');
        mobileNavBtn2026.classList.remove('active');
        if (mobileNavBackdrop2026) mobileNavBackdrop2026.classList.remove('active-backdrop-2026');
        console.log('Panel closed');
      } else {
        // Open
        mobileNavPanel2026.classList.add('active-panel-2026');
        mobileNavBtn2026.classList.add('active');
        if (mobileNavBackdrop2026) mobileNavBackdrop2026.classList.add('active-backdrop-2026');
        console.log('Panel opened');
      }
      
      console.log('Panel after toggle:', mobileNavPanel2026.className);
      console.log('Has active class?', mobileNavPanel2026.classList.contains('active-panel-2026'));
      
      // Log computed transform after a brief delay to see the transition
      setTimeout(() => {
        const newStyle = window.getComputedStyle(mobileNavPanel2026);
        console.log('Panel transform after:', newStyle.transform);
        console.log('Panel visibility after:', newStyle.visibility);
        console.log('Panel opacity after:', newStyle.opacity);
      }, 50);
    });
    
    // Close panel
    if (mobileNavClose2026) {
      mobileNavClose2026.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('🔴 Close button clicked');
        mobileNavPanel2026.classList.remove('active-panel-2026');
        mobileNavBtn2026.classList.remove('active');
        if (mobileNavBackdrop2026) mobileNavBackdrop2026.classList.remove('active-backdrop-2026');
      });
    }
    
    // Close when clicking backdrop
    if (mobileNavBackdrop2026) {
      mobileNavBackdrop2026.addEventListener('click', function(e) {
        console.log('🔴 Backdrop clicked');
        mobileNavPanel2026.classList.remove('active-panel-2026');
        mobileNavBtn2026.classList.remove('active');
        mobileNavBackdrop2026.classList.remove('active-backdrop-2026');
      });
    }
    
    // Prevent closing when clicking inside panel
    mobileNavPanel2026.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  } else {
    if (!mobileNavBtn2026) {
      console.log('ℹ️ Ellipsis button not rendered (breadcrumb length <= 3)');
    } else {
      console.error('❌ Mobile nav panel not found!');
    }
  }
  
  // ==========================================
  // DRAG AND DROP FOR MOBILE NAV
  // ==========================================
  if (!FM.isReadonly && mobileNavBtn2026 && mobileNavPanel2026) {
    // Ellipsis button drop target
    mobileNavBtn2026.addEventListener('dragenter', function(e) {
      e.preventDefault();
      e.stopPropagation();
      mobileNavPanel2026.classList.add('active-panel-2026');
      mobileNavBtn2026.classList.add('drag-over');
    });
    
    mobileNavBtn2026.addEventListener('dragleave', function(e) {
      e.preventDefault();
      mobileNavBtn2026.classList.remove('drag-over');
    });
    
    mobileNavBtn2026.addEventListener('dragover', function(e) {
      e.preventDefault();
    });
    
    mobileNavBtn2026.addEventListener('drop', function(e) {
      e.preventDefault();
      mobileNavBtn2026.classList.remove('drag-over');
    });
    
    // Panel folders drop targets
    const dropFolders2026 = document.querySelectorAll('.breadcrumb-mobile-dropdown-item-2026.folder-dropzone');
    dropFolders2026.forEach(folder => {
      folder.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('drag-over');
      });
      
      folder.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
      });
      
      folder.addEventListener('dragover', function(e) {
        e.preventDefault();
      });
      
      folder.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        const targetFolderId = this.dataset.folderId;
        const targetFolderType = this.dataset.folderType;
        
        if (FM.dragData && FM.dragData.ids && FM.dragData.ids.length > 0) {
          handleDrop(targetFolderId, targetFolderType);
          
          setTimeout(() => {
            mobileNavPanel2026.classList.remove('active-panel-2026');
            if (mobileNavBtn2026) mobileNavBtn2026.classList.remove('active');
          }, 300);
        }
      });
    });
  }
  
  // Run on load and resize
  handleBreadcrumbOverflow();
  window.addEventListener('resize', handleBreadcrumbOverflow);
  
  // ==========================================
  // SELECTION HANDLING
  // ==========================================
  function updateSelectionUI() {
    const count = selectedItems.size;
    
    if (count > 0) {
      if (selectionActions) selectionActions.style.display = 'flex';
      if (normalActions) normalActions.style.display = 'none';
      if (selectionCount) selectionCount.textContent = `${count} selected`;
    } else {
      if (selectionActions) selectionActions.style.display = 'none';
      if (normalActions) normalActions.style.display = 'flex';
    }
    
    // Update item visual state
    items.forEach(item => {
      const id = item.dataset.id;
      const type = item.dataset.type;
      const key = `${type}-${id}`;
      
      if (selectedItems.has(key)) {
        item.classList.add('selected');
      } else {
        item.classList.remove('selected');
      }
    });
  }
  
  // Checkbox change handler
  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const id = this.dataset.id;
      const type = this.dataset.type;
      const key = `${type}-${id}`;
      
      if (this.checked) {
        selectedItems.add(key);
      } else {
        selectedItems.delete(key);
      }
      
      updateSelectionUI();
    });
  });
  
  // Item click handler (for mobile touch)
  items.forEach(item => {
    item.addEventListener('click', function(e) {
      // Only on mobile or when in selection mode
      if (window.innerWidth <= 768 || selectedItems.size > 0) {
        if (!e.target.closest('a') && !e.target.closest('.fm-item-actions') && !e.target.closest('.fm-checkbox')) {
          const checkbox = this.querySelector('.fm-checkbox');
          if (checkbox) {
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change'));
            e.preventDefault();
          }
        }
      }
    });
  });
  
  // Select All buttons
  document.querySelectorAll('.fm-select-all-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const type = this.dataset.type;
      const typeCheckboxes = document.querySelectorAll(`.fm-checkbox[data-type="${type}"]`);
      
      const allChecked = Array.from(typeCheckboxes).every(cb => cb.checked);
      
      typeCheckboxes.forEach(cb => {
        cb.checked = !allChecked;
        cb.dispatchEvent(new Event('change'));
      });
    });
  });
  
  // Cancel selection
  const cancelBtn = document.getElementById('cancelSelectionBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function() {
      checkboxes.forEach(cb => {
        cb.checked = false;
      });
      selectedItems.clear();
      updateSelectionUI();
    });
  }
  
  // ==========================================
  // ACTIONS: CUT, COPY, DELETE
  // ==========================================
  const cutBtn = document.getElementById('cutBtn');
  if (cutBtn) {
    cutBtn.addEventListener('click', function() {
      if (selectedItems.size === 0) return;
      
      clipboardItems = Array.from(selectedItems);
      clipboardAction = 'cut';
      
      if (window.notify) {
        window.notify(`${selectedItems.size} item(s) cut. Navigate to destination and paste.`, 'info');
      } else {
        alert(`${selectedItems.size} item(s) cut`);
      }
      
      // Visual feedback
      items.forEach(item => {
        const key = `${item.dataset.type}-${item.dataset.id}`;
        if (selectedItems.has(key)) {
          item.style.opacity = '0.5';
        }
      });
    });
  }
  
  const copyBtn = document.getElementById('copyBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      if (selectedItems.size === 0) return;
      
      clipboardItems = Array.from(selectedItems);
      clipboardAction = 'copy';
      
      if (window.notify) {
        window.notify(`${selectedItems.size} item(s) copied. Navigate to destination and paste.`, 'info');
      } else {
        alert(`${selectedItems.size} item(s) copied`);
      }
    });
  }
  
  const deleteBtn = document.getElementById('deleteBtn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', function() {
      if (selectedItems.size === 0) return;
      
      if (!confirm(`Are you sure you want to delete ${selectedItems.size} item(s)?`)) {
        return;
      }
      
      const itemsToDelete = Array.from(selectedItems);
      let deletePromises = [];
      
      // Delete each item individually using the appropriate URL
      itemsToDelete.forEach(key => {
        const [type, id] = key.split('-');
        const url = type === 'file' ? urls.deleteFile : urls.deleteFolder;
        const param = type === 'file' ? 'attachment_id' : 'folder_id';
        
        if (!url) {
          console.error(`Delete URL not found for type: ${type}`);
          return;
        }
        
        const formData = new FormData();
        formData.append(param, id);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        const promise = fetch(url, {
          method: 'POST',
          body: formData
        }).then(response => response.json());
        
        deletePromises.push(promise);
      });
      
      // Wait for all deletions to complete
      Promise.all(deletePromises)
        .then(results => {
          const allSuccess = results.every(data => data.success);
          
          if (allSuccess) {
            if (window.notify) {
              window.notify(`Successfully deleted ${itemsToDelete.length} item(s)`, 'success');
            } else {
              alert(`Successfully deleted ${itemsToDelete.length} item(s)`);
            }
            setTimeout(() => location.reload(), 500);
          } else {
            const failedCount = results.filter(data => !data.success).length;
            if (window.notify) {
              window.notify(`Failed to delete ${failedCount} item(s)`, 'error');
            } else {
              alert(`Failed to delete ${failedCount} item(s)`);
            }
          }
        })
        .catch(error => {
          console.error('Delete error:', error);
          if (window.notify) {
            window.notify(`An error occurred: ${error.message}`, 'error');
          } else {
            alert(`An error occurred: ${error.message}`);
          }
        });
    });
  }
  
  // ==========================================
  // CREATE FOLDER
  // ==========================================
  const createFolderBtn = document.getElementById('createFolderBtn');
  if (createFolderBtn && createFolderModal) {
    createFolderBtn.addEventListener('click', function() {
      createFolderModal.show();
    });
  }
  
  const emptyCreateFolderBtn = document.getElementById('emptyCreateFolderBtn');
  if (emptyCreateFolderBtn && createFolderModal) {
    emptyCreateFolderBtn.addEventListener('click', function() {
      createFolderModal.show();
    });
  }
  
  // ==========================================
  // VIEW TOGGLE (Grid/List)
  // ==========================================
  function applyView(view) {
    const grids = document.querySelectorAll('.fm-grid');
    
    grids.forEach(grid => {
      if (view === 'list') {
        grid.classList.add('list-view');
      } else {
        grid.classList.remove('list-view');
      }
    });
  }
  
  // Restore saved view preference
  const savedView = localStorage.getItem('fileManagerView') || 'grid';
  document.querySelectorAll('.fm-view-btn').forEach(btn => {
    if (btn.dataset.view === savedView) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  applyView(savedView);
  
  // View toggle buttons
  document.querySelectorAll('.fm-view-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.fm-view-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      const view = this.dataset.view;
      localStorage.setItem('fileManagerView', view);
      applyView(view);
    });
  });
  
  // ==========================================
  // MOBILE: Hide view toggle
  // ==========================================
  function handleMobileViewToggle() {
    const viewToggle = document.querySelector('.fm-view-toggle');
    if (viewToggle) {
      if (window.innerWidth <= 768) {
        viewToggle.style.display = 'none';
      } else {
        viewToggle.style.display = 'flex';
      }
    }
  }
  
  handleMobileViewToggle();
  window.addEventListener('resize', handleMobileViewToggle);
});
