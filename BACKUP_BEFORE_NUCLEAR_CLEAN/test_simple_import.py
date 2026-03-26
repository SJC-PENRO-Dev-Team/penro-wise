import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

try:
    from document_tracking.email_service_test import TestEmailService
    print("SUCCESS: TestEmailService imported successfully")
    print(f"Result: {TestEmailService.test_method()}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
