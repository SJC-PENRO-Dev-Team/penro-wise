/**
 * Users Page Scripts
 * Handles dropdown filters, user creation, and onboarding flow
 */
document.addEventListener("DOMContentLoaded", function () {

  /* =====================================================
     GUARD: prevent double-binding
  ===================================================== */
  if (window.__userScriptsLoaded) return;
  window.__userScriptsLoaded = true;

  /* =====================================================
     MODAL INITIALIZATION - PREVENT FLASH
  ===================================================== */
  // Ensure all modals are properly hidden on page load
  document.querySelectorAll('.modal').forEach(modal => {
    // Remove any lingering 'show' class
    modal.classList.remove('show');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    
    // Remove any lingering backdrop
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) backdrop.remove();
  });
  
  // Remove body modal-open class if present
  document.body.classList.remove('modal-open');
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';

  /* =====================================================
     DROPDOWN FILTER HANDLERS
  ===================================================== */
  function initializeDropdowns() {
    // Handle both workcycle filters and user filters
    document.querySelectorAll(".wc-filter-dropdown .wc-filter-btn, .filter-dropdown .filter-btn")
      .forEach(button => {
        button.addEventListener("click", e => {
          e.preventDefault();
          e.stopPropagation();

          const dropdown = button.closest(".wc-filter-dropdown, .filter-dropdown");
          const isOpen = dropdown.classList.contains("open");

          document.querySelectorAll(".wc-filter-dropdown, .filter-dropdown")
            .forEach(d => d.classList.remove("open"));

          if (!isOpen) dropdown.classList.add("open");
        });
      });

    document.addEventListener("click", e => {
      if (!e.target.closest(".wc-filter-dropdown") && !e.target.closest(".filter-dropdown")) {
        document.querySelectorAll(".wc-filter-dropdown, .filter-dropdown")
          .forEach(d => d.classList.remove("open"));
      }
    });

    document.addEventListener("keydown", e => {
      if (e.key === "Escape") {
        document.querySelectorAll(".wc-filter-dropdown, .filter-dropdown")
          .forEach(d => d.classList.remove("open"));
      }
    });
  }

  initializeDropdowns();

  /* =====================================================
     CREATE USER SUBMIT (ABSOLUTE HARD GATE)
  ===================================================== */
  const createForm = document.getElementById("createUserForm");
  const createModalEl = document.getElementById("createUserModal");

  if (createForm) {
    createForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const submitBtn = createForm.querySelector('button[type="submit"]');
      if (submitBtn.disabled) return;

      const originalHTML = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

      // Clear previous errors
      createForm.querySelectorAll(".error-message").forEach(el => el.remove());
      createForm.querySelectorAll(".error").forEach(el =>
        el.classList.remove("error")
      );

      let response;
      try {
        response = await fetch(createForm.action, {
          method: "POST",
          body: new FormData(createForm),
          headers: { "X-Requested-With": "XMLHttpRequest" }
        });
      } catch (networkError) {
        console.error("Network error:", networkError);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
        return;
      }

      /* -------------------------------------------------
         SAFE JSON PARSE (NO CRASHES)
      ------------------------------------------------- */
      let data = {};
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        try {
          data = await response.json();
        } catch {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalHTML;
          return;
        }
      } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
        return;
      }

      /* -------------------------------------------------
         ❌ HARD STOP — ANY ERROR BLOCKS ONBOARDING
      ------------------------------------------------- */
      if (!response.ok || data.success !== true) {

        if (data.errors) {
          Object.entries(data.errors).forEach(([field, messages]) => {
            const input = createForm.querySelector(`[name="${field}"]`);
            if (!input) return;

            input.classList.add("error");

            const msg = document.createElement("div");
            msg.className = "error-message";
            msg.textContent = messages[0];

            input.closest(".form-field")?.appendChild(msg);
          });
        }

        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
      /* -------------------------------------------------
         ✅ SUCCESS → REDIRECT TO PROFILE
      ------------------------------------------------- */
      } else {
        const createModal = bootstrap.Modal.getInstance(createModalEl);
        if (createModal) {
          createModal.hide();
        }

        // Wait for modal to fully close before redirecting
        setTimeout(() => {
          if (data.profile_url) {
            // Redirect to the user profile page where they can set organization
            window.location.href = data.profile_url;
          }
        }, 400);

        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
      }
    });
  }

  /* =====================================================
     MODAL CLEANUP ON HIDE
  ===================================================== */
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('hidden.bs.modal', function () {
      // Clean up any lingering backdrops
      document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
      document.body.classList.remove('modal-open');
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    });
  });

});
