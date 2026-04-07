document.addEventListener("DOMContentLoaded", () => {
  const shell = document.querySelector("[data-app-shell]");
  if (!shell) {
    return;
  }

  const sidebar = shell.querySelector("[data-app-sidebar]");
  const sidebarBackdrop = shell.querySelector("[data-app-sidebar-backdrop]");
  const sidebarToggles = shell.querySelectorAll("[data-app-sidebar-toggle]");

  function closeNotifPanels() {
    document.querySelectorAll("[data-notif-dropdown].show").forEach((panel) => {
      panel.classList.remove("show");
    });

    document.querySelectorAll("[data-notif-toggle].active").forEach((button) => {
      button.classList.remove("active");
      button.setAttribute("aria-expanded", "false");
    });

    document.querySelectorAll("[data-notif-backdrop].show").forEach((backdrop) => {
      backdrop.classList.remove("show");
    });
  }

  function openSidebar() {
    shell.classList.add("is-sidebar-open");
    sidebarBackdrop?.classList.add("is-visible");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    shell.classList.remove("is-sidebar-open");
    sidebarBackdrop?.classList.remove("is-visible");
    document.body.style.overflow = "";
  }

  sidebarToggles.forEach((button) => {
    button.addEventListener("click", () => {
      if (shell.classList.contains("is-sidebar-open")) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  });

  sidebarBackdrop?.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSidebar();
      closeNotifPanels();
    }
  });

  if (sidebar) {
    sidebar.querySelectorAll("[data-nav-group-toggle]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const group = toggle.closest("[data-nav-group]");
        if (!group) {
          return;
        }

        const expanded = group.classList.toggle("is-expanded");
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
      });
    });

    sidebar.querySelectorAll("a[href]").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 991.98) {
          closeSidebar();
        }
      });
    });
  }

  window.addEventListener("resize", () => {
    if (window.innerWidth > 991.98) {
      closeSidebar();
    }
  });
});
