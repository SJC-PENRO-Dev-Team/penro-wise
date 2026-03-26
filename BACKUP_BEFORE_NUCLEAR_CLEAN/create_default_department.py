"""
Create Default Workforces Department

Run this after migrations to create the default department.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkforcesDepartment, User

def create_default_department():
    """Create the default Workforces Department."""
    print("=" * 70)
    print("CREATE DEFAULT WORKFORCES DEPARTMENT")
    print("=" * 70)
    print()
    
    # Check if department already exists
    existing = WorkforcesDepartment.objects.first()
    if existing:
        print(f"✅ Department already exists: {existing.name}")
        print(f"   ID: {existing.id}")
        print(f"   Active: {existing.is_active}")
        print(f"   Created: {existing.created_at}")
        return existing
    
    # Create new department
    print("Creating default department...")
    department = WorkforcesDepartment.objects.create(
        name="Workforces Department",
        description="Unified department for all workforce members",
        is_active=True
    )
    
    print()
    print("✅ Department created successfully!")
    print(f"   Name: {department.name}")
    print(f"   ID: {department.id}")
    print(f"   Description: {department.description}")
    print()
    
    return department

def assign_existing_users(department):
    """Assign all existing users to the department."""
    print("=" * 70)
    print("ASSIGN EXISTING USERS TO DEPARTMENT")
    print("=" * 70)
    print()
    
    users_without_dept = User.objects.filter(department__isnull=True)
    count = users_without_dept.count()
    
    if count == 0:
        print("✅ All users already have department assignments")
        return
    
    print(f"Found {count} users without department assignment")
    print()
    
    response = input(f"Assign all {count} users to '{department.name}'? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("❌ Skipped user assignment")
        return
    
    # Assign users
    updated = users_without_dept.update(department=department)
    
    print()
    print(f"✅ Assigned {updated} users to department")
    print()

def show_summary():
    """Show summary of departments and users."""
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    # Departments
    departments = WorkforcesDepartment.objects.all()
    print(f"Total Departments: {departments.count()}")
    for dept in departments:
        member_count = dept.members.count()
        print(f"  • {dept.name} ({member_count} members)")
    print()
    
    # Users
    total_users = User.objects.count()
    users_with_dept = User.objects.filter(department__isnull=False).count()
    users_without_dept = User.objects.filter(department__isnull=True).count()
    
    print(f"Total Users: {total_users}")
    print(f"  • With department: {users_with_dept}")
    print(f"  • Without department: {users_without_dept}")
    print()

def main():
    try:
        # Create department
        department = create_default_department()
        
        # Assign existing users
        assign_existing_users(department)
        
        # Show summary
        show_summary()
        
        print("=" * 70)
        print("✅ SETUP COMPLETE")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Create superuser: python manage.py createsuperuser")
        print("2. Start server: python manage.py runserver")
        print("3. Update views and forms to use WorkforcesDepartment")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"{type(e).__name__}: {e}")
        print()
        print("Make sure you have:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Database is accessible")
        print()

if __name__ == "__main__":
    main()
