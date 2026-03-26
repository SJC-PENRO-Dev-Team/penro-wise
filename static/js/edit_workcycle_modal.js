/* ===== EDIT WORKCYCLE MODAL JAVASCRIPT ===== */

document.addEventListener("DOMContentLoaded", () => {
  const editModal = document.getElementById("editWorkcycleModal");
  if (!editModal) return;

  // Initialize flatpickr for due date
  flatpickr("#editDueDate", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
    time_24hr: true,
    minuteIncrement: 5
  });

  // Populate modal when opened
  editModal.addEventListener("show.bs.modal", function (event) {
    const btn = event.relatedTarget;

    document.getElementById("editWorkcycleId").value = btn.dataset.id || "";
    document.getElementById("editTitle").value = btn.dataset.title || "";
    document.getElementById("editDescription").value = btn.dataset.description || "";
    document.getElementById("editDueDate").value = btn.dataset.due || "";
    document.getElementById("editContextTitle").textContent = btn.dataset.title || "Work Cycle Details";
  });
});
