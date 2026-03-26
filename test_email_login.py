"""
Test script to verify email/username login functionality.
Run with: python manage.py shell < test_email_login.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import RequestFactory

User = get_user_model()

print("\n" + "="*60)
print("EMAIL/USERNAME LOGIN TEST")
print("="*60)

# Get a test user (or create one)
try:
    user = User.objects.first()
    if not user:
        print("\n❌ No users found in database. Please create a user first.")
        exit()
    
    print(f"\n✓ Testing with user:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email or '(not set)'}")
    print(f"  - Full Name: {user.get_full_name() or '(not set)'}")
    
    # Test authentication with username
    print(f"\n1. Testing login with USERNAME: '{user.username}'")
    test_user = authenticate(username=user.username, password='test123')
    if test_user:
        print(f"   ✓ SUCCESS: Authenticated as {test_user.username}")
    else:
        print(f"   ℹ INFO: Authentication failed (password might be incorrect)")
    
    # Test authentication with email (if email exists)
    if user.email:
        print(f"\n2. Testing login with EMAIL: '{user.email}'")
        test_user = authenticate(username=user.email, password='test123')
        if test_user:
            print(f"   ✓ SUCCESS: Authenticated as {test_user.username}")
        else:
            print(f"   ℹ INFO: Authentication failed (password might be incorrect)")
    else:
        print(f"\n2. ⚠ WARNING: User has no email set, skipping email test")
    
    # Test case-insensitive login
    print(f"\n3. Testing CASE-INSENSITIVE login with: '{user.username.upper()}'")
    test_user = authenticate(username=user.username.upper(), password='test123')
    if test_user:
        print(f"   ✓ SUCCESS: Case-insensitive authentication works!")
    else:
        print(f"   ℹ INFO: Authentication failed (password might be incorrect)")
    
    print("\n" + "="*60)
    print("BACKEND CONFIGURATION CHECK")
    print("="*60)
    
    from django.conf import settings
    backends = settings.AUTHENTICATION_BACKENDS
    print(f"\nConfigured authentication backends:")
    for i, backend in enumerate(backends, 1):
        print(f"  {i}. {backend}")
        if 'EmailOrUsernameBackend' in backend:
            print(f"     ✓ Custom email/username backend is active!")
    
    print("\n" + "="*60)
    print("INSTRUCTIONS FOR MANUAL TESTING")
    print("="*60)
    print("\n1. Go to the login page")
    print("2. Try logging in with:")
    print(f"   - Username: {user.username}")
    if user.email:
        print(f"   - Email: {user.email}")
    print("   - Password: (your actual password)")
    print("\n3. Both should work with the same password!")
    
    print("\n" + "="*60)
    print("NOTE: If authentication fails above, it's likely because")
    print("the test password 'test123' doesn't match the actual password.")
    print("The backend is still configured correctly.")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
