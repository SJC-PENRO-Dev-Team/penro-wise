/**
 * Message Modal - Floating Chat Panel
 * Separated from message_ui_modal.html for faster loading
 */
(function () {
  'use strict';

  function init() {
    const modal = document.getElementById('msgDiscussionModal');
    if (!modal) return;

    const iframe = modal.querySelector('#msgModalFrame');
    const loader = modal.querySelector('#msgModalLoader');
    const closeBtn = modal.querySelector('[data-msg-dismiss]');
    const titleEl = modal.querySelector('#msgModalTitle');
    const subtitleEl = modal.querySelector('#msgModalSubtitle');

    let hasValidUrl = false;
    let currentUrl = '';
    let loadRetryCount = 0;
    const MAX_RETRIES = 2;

    modal.setAttribute('data-msg-state', 'closed');
    if (iframe) iframe.style.display = 'none';

    function showLoader(message) {
      if (loader) {
        loader.removeAttribute('data-msg-hidden');
        const loaderText = loader.querySelector('span');
        if (loaderText) loaderText.textContent = message || 'Loading messages...';
      }
    }

    function hideLoader() {
      if (loader) loader.setAttribute('data-msg-hidden', 'true');
    }

    function showError(message) {
      hideLoader();
      if (iframe) iframe.style.display = 'none';
      
      let errorDiv = modal.querySelector('.msg-modal-error');
      const modalBody = modal.querySelector('.msg-modal-body');
      
      if (!errorDiv && modalBody) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'msg-modal-error';
        errorDiv.style.cssText = 'position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;background:#f8fafc;color:#64748b;font-size:14px;font-weight:500;text-align:center;padding:20px;';
        modalBody.appendChild(errorDiv);
      }
      
      if (errorDiv) {
        errorDiv.innerHTML = '<div style="width:56px;height:56px;border-radius:50%;background:#fee2e2;display:flex;align-items:center;justify-content:center;"><i class="fas fa-exclamation-triangle" style="font-size:24px;color:#ef4444;"></i></div><div style="color:#475569;font-weight:600;">' + message + '</div><button onclick="window.msgDiscussion.retry()" style="background:linear-gradient(135deg,#3b82f6 0%,#2563eb 100%);color:white;border:none;padding:10px 24px;border-radius:8px;font-weight:600;cursor:pointer;font-size:13px;"><i class="fas fa-redo" style="margin-right:6px;"></i> Try Again</button>';
        errorDiv.style.display = 'flex';
      }
    }

    function hideError() {
      const errorDiv = modal.querySelector('.msg-modal-error');
      if (errorDiv) errorDiv.style.display = 'none';
    }

    function openModal(url, title, subtitle) {
      if (!url) return;

      hasValidUrl = true;
      currentUrl = url;
      loadRetryCount = 0;
      
      hideError();
      showLoader('Loading messages...');
      
      if (iframe) {
        iframe.removeAttribute('data-msg-loaded');
        iframe.style.display = 'block';
        iframe.src = url;
      }

      if (titleEl) titleEl.textContent = title || 'Discussion';
      if (subtitleEl) subtitleEl.textContent = subtitle || '';

      modal.setAttribute('data-msg-state', 'open');
      document.body.style.overflow = 'hidden';
    }

    function retryLoad() {
      if (!currentUrl || loadRetryCount >= MAX_RETRIES) {
        showError('Unable to load. Please close and try again.');
        return;
      }
      
      loadRetryCount++;
      hideError();
      showLoader('Retrying...');
      if (iframe) {
        iframe.style.display = 'block';
        iframe.src = currentUrl;
      }
    }

    function closeModal() {
      modal.setAttribute('data-msg-state', 'closed');
      document.body.style.overflow = '';

      setTimeout(function () {
        hasValidUrl = false;
        currentUrl = '';
        loadRetryCount = 0;
        if (iframe) {
          iframe.src = 'about:blank';
          iframe.style.display = 'none';
        }
        hideError();
        window.location.reload();
      }, 400);
    }

    if (iframe) {
      iframe.addEventListener('load', function () {
        if (!hasValidUrl || modal.getAttribute('data-msg-state') !== 'open') return;
        
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
          
          if (iframeDoc && iframeDoc.body) {
            const bodyText = iframeDoc.body.innerText || '';
            
            if (bodyText.includes('refused to connect') || 
                bodyText.includes('ERR_CONNECTION_REFUSED') ||
                bodyText.includes("This site can't be reached")) {
              showError('Connection failed. Server may be busy.');
              return;
            }
          }
          
          hideLoader();
          hideError();
          iframe.setAttribute('data-msg-loaded', 'true');
          
        } catch (e) {
          hideLoader();
          hideError();
          iframe.setAttribute('data-msg-loaded', 'true');
        }
      });

      iframe.addEventListener('error', function () {
        if (hasValidUrl && modal.getAttribute('data-msg-state') === 'open') {
          showError('Failed to load discussion.');
        }
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modal.getAttribute('data-msg-state') === 'open') {
        closeModal();
      }
    });

    function attachTriggers() {
      document.querySelectorAll('[data-qxdlg-trigger]').forEach(function (trigger) {
        if (trigger.hasAttribute('data-msg-bound')) return;
        trigger.setAttribute('data-msg-bound', 'true');

        trigger.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          
          const url = this.getAttribute('data-qxdlg-url');
          const title = this.getAttribute('data-qxdlg-title');
          const subtitle = this.getAttribute('data-qxdlg-subtitle');
          
          openModal(url, title, subtitle);
        });
      });
    }

    attachTriggers();

    window.msgDiscussion = {
      open: openModal,
      close: closeModal,
      retry: retryLoad,
      attachTriggers: attachTriggers
    };

    window.qxdlgDiscussion = window.msgDiscussion;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  window.addEventListener('load', function() {
    if (window.msgDiscussion && typeof window.msgDiscussion.attachTriggers === 'function') {
      window.msgDiscussion.attachTriggers();
    } else {
      init();
    }
  });
})();
