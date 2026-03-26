/* ===== REASSIGN WORKCYCLE MODAL JAVASCRIPT ===== */

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("reassignWorkcycleModal");
  if (!modal) return;

  const idInput = document.getElementById("reassignWorkcycleId");
  const titleEl = document.getElementById("reassignWorkcycleTitle");
  const currentEl = document.getElementById("currentAssignment");
  const userList = document.getElementById("reassignUserList");
  const addUserBtn = document.getElementById("reassignAddUserBtn");
  const teamSelect = document.getElementById("reassignTeamSelect");
  const usersSection = document.getElementById("reassignUsersSection");
  const teamSection = document.getElementById("reassignTeamSection");

  /* ===== HELPERS ===== */
  function hasAssignedUsers() {
    return [...userList.querySelectorAll(".user-hidden")]
      .some(i => i.value);
  }

  function getSelectedUserIds() {
    return [...userList.querySelectorAll(".user-hidden")]
      .map(i => i.value)
      .filter(Boolean);
  }

  function refreshDropdowns() {
    const selected = getSelectedUserIds();

    userList.querySelectorAll(".user-row").forEach(row => {
      const hidden = row.querySelector(".user-hidden");
      const options = row.querySelectorAll(".user-option");

      options.forEach(opt => {
        const id = opt.dataset.id;
        opt.dataset.blocked =
          selected.includes(id) && hidden.value !== id ? "1" : "0";
      });
    });
  }

  function toggleAssignSections() {
    const usersSelected = hasAssignedUsers();
    const teamSelected = teamSelect.value !== "";

    teamSection.style.display = usersSelected ? "none" : "block";
    usersSection.style.display = teamSelected ? "none" : "block";

    if (usersSelected) {
      teamSelect.value = "";
    }

    if (teamSelected && document.activeElement === teamSelect) {
      document.querySelectorAll(".user-hidden").forEach(i => i.value = "");
      document.querySelectorAll(".user-input").forEach(i => i.value = "");
    }
  }

  /* ===== USER COMBO BEHAVIOR ===== */
  function attachUserCombo(row) {
    const combo = row.querySelector(".user-combo");
    if (!combo) return;

    const input = combo.querySelector(".user-input");
    const hidden = combo.querySelector(".user-hidden");
    const dropdown = combo.querySelector(".user-dropdown");
    const options = [...combo.querySelectorAll(".user-option")];

    input.addEventListener("focus", () => {
      refreshDropdowns();
      dropdown.style.display = "block";

      options.forEach(opt => {
        opt.style.display = opt.dataset.blocked === "1" ? "none" : "block";
      });
    });

    combo.addEventListener("click", () => input.focus());

    input.addEventListener("input", () => {
      const q = input.value.toLowerCase();

      options.forEach(opt => {
        if (opt.dataset.blocked === "1") {
          opt.style.display = "none";
          return;
        }

        opt.style.display = opt.dataset.label.toLowerCase().includes(q)
          ? "block"
          : "none";
      });
    });

    options.forEach(opt => {
      opt.addEventListener("click", () => {
        hidden.value = opt.dataset.id;
        input.value = opt.dataset.label;
        dropdown.style.display = "none";

        const row = combo.closest(".user-row");
        row.querySelector(".remove-user").style.display = "inline-block";

        refreshDropdowns();
        toggleAssignSections();
      });
    });

    document.addEventListener("click", e => {
      if (!combo.contains(e.target)) dropdown.style.display = "none";
    });
  }

  /* ===== ADD USER ROW ===== */
  addUserBtn.addEventListener("click", () => {
    const row = userList.firstElementChild.cloneNode(true);

    row.querySelector(".user-input").value = "";
    row.querySelector(".user-hidden").value = "";
    row.querySelector(".user-dropdown").style.display = "none";
    row.querySelector(".remove-user").style.display = "inline-block";

    userList.appendChild(row);
    attachUserCombo(row);
    refreshDropdowns();
  });

  /* ===== REMOVE / CLEAR USER ROW ===== */
  userList.addEventListener("click", e => {
    if (!e.target.classList.contains("remove-user")) return;

    const row = e.target.closest(".user-row");
    const rows = userList.querySelectorAll(".user-row");

    if (rows.length === 1) {
      row.querySelector(".user-hidden").value = "";
      row.querySelector(".user-input").value = "";
      row.querySelector(".user-dropdown").style.display = "none";
      row.querySelector(".remove-user").style.display = "none";
    } else {
      row.remove();
    }

    setTimeout(() => {
      refreshDropdowns();
      toggleAssignSections();
    }, 0);
  });

  /* ===== TEAM CHANGE ===== */
  teamSelect.addEventListener("change", toggleAssignSections);

  /* ===== MODAL OPEN / RESET ===== */
  modal.addEventListener("show.bs.modal", (event) => {
    const btn = event.relatedTarget;

    // Debug logging
    console.log("Reassign Modal Data:", {
      id: btn.dataset.id,
      title: btn.dataset.title,
      users: btn.dataset.users,
      teams: btn.dataset.teams
    });

    idInput.value = btn.dataset.id || "";
    titleEl.textContent = btn.dataset.title || "—";
    currentEl.innerHTML = "";

    const users = (btn.dataset.users || "")
      .split("|").map(v => v.trim()).filter(Boolean);

    const teams = (btn.dataset.teams || "")
      .split("|").map(v => v.trim()).filter(Boolean);

    console.log("Parsed assignments:", { users, teams });

    if (!users.length && !teams.length) {
      currentEl.innerHTML = `
        <span class="assignment-pill empty">
          <i class="far fa-user"></i> No assignment
        </span>`;
    }

    users.forEach(name => {
      currentEl.insertAdjacentHTML("beforeend", `
        <span class="assignment-pill user">
          <i class="far fa-user"></i> ${name}
        </span>
      `);
    });

    teams.forEach(name => {
      currentEl.insertAdjacentHTML("beforeend", `
        <span class="assignment-pill team">
          <i class="fas fa-users"></i> ${name}
        </span>
      `);
    });

    // Reset assignment UI
    teamSelect.value = "";
    userList.innerHTML = userList.firstElementChild.outerHTML;

    attachUserCombo(userList.firstElementChild);
    refreshDropdowns();
    toggleAssignSections();
  });

  /* ===== MUTATION OBSERVER FOR DYNAMIC ROWS ===== */
  const observer = new MutationObserver(muts => {
    muts.forEach(m =>
      m.addedNodes.forEach(n => {
        if (n.classList?.contains("user-row")) {
          attachUserCombo(n);
          refreshDropdowns();
        }
      })
    );
  });

  observer.observe(userList, {
    childList: true
  });

  // Initialize first row
  attachUserCombo(userList.firstElementChild);
});
