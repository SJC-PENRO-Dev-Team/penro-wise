import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

try:
    from document_tracking.email_service import DocumentTrackingEmailService
    print("SUCCESS: DocumentTrackingEmailService imported successfully")
    print(f"Class: {DocumentTrackingEmailService}")
    print(f"Methods: {dir(DocumentTrackingEmailService)}")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"OTHER ERROR: {e}")
    import traceback
    traceback.print_exc()
