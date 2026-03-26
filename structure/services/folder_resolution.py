from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from structure.models import DocumentFolder


# ============================================================
# PERMISSION CHECK
# ============================================================

def assert_can_upload(*, work_item, actor):
    """
    Admins can upload anything.
    Users can only upload to their own work items.
    """
    if actor.login_role == "admin":
        return

    if work_item.owner_id != actor.id:
        raise PermissionDenied(
            "You are not allowed to upload attachments for this work item."
        )


# ============================================================
# SAFE FOLDER CREATION
# ============================================================
def get_or_create_folder(
    *,
    name,
    folder_type,
    parent,
    workcycle=None,
    workforces_department=None,
    created_by=None,
    system=True,
):
    """
    Creates or retrieves a DocumentFolder safely.

    RULES (ENFORCED):
    - (parent, name) uniqueness
    - ONLY WORKCYCLE folders may have `workcycle` set
    - ONLY WORKFORCES_DEPARTMENT folders may have `workforces_department` set
    """

    # -------------------------------------------------
    # SANITY: enforce model invariant at service level
    # -------------------------------------------------
    if folder_type != DocumentFolder.FolderType.WORKCYCLE and workcycle is not None:
        workcycle = None  # hard guarantee

    if folder_type != DocumentFolder.FolderType.WORKFORCES_DEPARTMENT and workforces_department is not None:
        workforces_department = None  # hard guarantee

    # -------------------------------------------------
    # CREATE OR GET
    # -------------------------------------------------
    folder, created = DocumentFolder.objects.get_or_create(
        parent=parent,
        name=name,
        defaults={
            "folder_type": folder_type,
            "workcycle": workcycle,
            "workforces_department": workforces_department,
            "created_by": created_by,
            "is_system_generated": system,
        },
    )

    return folder

# ============================================================
# MAIN RESOLUTION SERVICE (SIMPLIFIED)
# ============================================================

@transaction.atomic
def resolve_attachment_folder(*, work_item, attachment_type, actor):
    """
    Resolves the attachment folder with simplified structure.

    NEW STRUCTURE:
    ROOT
      └─ YEAR
          └─ CATEGORY (attachment type)
              └─ WORKCYCLE
                  └─ WORKFORCES_DEPARTMENT

    RULES:
    - Single department per system
    - No organizational hierarchy
    - All files go to: ROOT > YEAR > CATEGORY > WORKCYCLE > WORKFORCES_DEPARTMENT
    """

    # -------------------------------------------------
    # 1️⃣ PERMISSION CHECK
    # -------------------------------------------------
    assert_can_upload(work_item=work_item, actor=actor)

    # -------------------------------------------------
    # 2️⃣ ROOT
    # -------------------------------------------------
    root = get_or_create_folder(
        name="ROOT",
        folder_type=DocumentFolder.FolderType.ROOT,
        parent=None,
    )

    # -------------------------------------------------
    # 3️⃣ YEAR (DERIVED FROM WORKCYCLE)
    # -------------------------------------------------
    year_folder = get_or_create_folder(
        name=str(work_item.workcycle.due_at.year),
        folder_type=DocumentFolder.FolderType.YEAR,
        parent=root,
    )

    # -------------------------------------------------
    # 4️⃣ CATEGORY (ATTACHMENT TYPE BUCKET)
    # -------------------------------------------------
    attachment_type_folder = get_or_create_folder(
        name=attachment_type.upper(),  # MATRIX_A, MATRIX_B, MOV
        folder_type=DocumentFolder.FolderType.CATEGORY,
        parent=year_folder,
    )

    # -------------------------------------------------
    # 5️⃣ WORKCYCLE
    # -------------------------------------------------
    workcycle_folder = get_or_create_folder(
        name=work_item.workcycle.title,
        folder_type=DocumentFolder.FolderType.WORKCYCLE,
        parent=attachment_type_folder,
        workcycle=work_item.workcycle,
    )

    # -------------------------------------------------
    # 6️⃣ WORKFORCES DEPARTMENT (SIMPLIFIED)
    # -------------------------------------------------
    
    # Get user's department or use default
    department = actor.department
    
    if not department:
        # Fallback: Get or create default department
        from accounts.models import WorkforcesDepartment
        department, _ = WorkforcesDepartment.objects.get_or_create(
            name="Workforces Department",
            defaults={
                "description": "Default department for all workforce members",
                "is_active": True,
            }
        )
    
    # Create department folder
    department_folder = get_or_create_folder(
        name=department.name,
        folder_type=DocumentFolder.FolderType.WORKFORCES_DEPARTMENT,
        parent=workcycle_folder,
        workforces_department=department,
    )

    return department_folder


# ============================================================
# DISPLAY / CONTEXT HELPERS (READ-ONLY)
# ============================================================

def acronym(name: str | None) -> str | None:
    """
    Converts:
    'Backend Development Unit' → 'BDU'
    """
    if not name:
        return None
    return "".join(word[0].upper() for word in name.split() if word)


def resolve_folder_context(folder: DocumentFolder | None):
    """
    READ-ONLY helper.

    Safely extracts workcycle + department structure
    from ANY folder depth.

    Returns:
    {
        workcycle,
        department,
    }
    """

    context = {
        "workcycle": None,
        "department": None,
    }

    if not folder:
        return context

    context["workcycle"] = folder.workcycle

    for f in folder.get_path():
        if f.folder_type == DocumentFolder.FolderType.WORKFORCES_DEPARTMENT:
            context["department"] = f.name

    return context


# ============================================================
# HELPER: UI PREVIEW (ACRONYM-BASED)
# ============================================================

def get_upload_path_preview(*, work_item, attachment_type, actor):
    """
    Returns a UI-friendly preview path using acronyms.

    Example:
    ROOT / 2026 / MATRIX_A / Q1 Report / Workforces Department
    """

    folder = resolve_attachment_folder(
        work_item=work_item,
        attachment_type=attachment_type,
        actor=actor,
    )

    ctx = resolve_folder_context(folder)

    parts = [
        "ROOT",
        str(ctx["workcycle"].due_at.year) if ctx["workcycle"] else None,
        attachment_type.upper(),
        ctx["workcycle"].title if ctx["workcycle"] else None,
        ctx["department"] or "Workforces Department",
    ]

    return " / ".join(p for p in parts if p)
