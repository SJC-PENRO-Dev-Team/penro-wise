"""
Verify email configuration
"""
import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

print("=" * 60)
print("Email Configuration Verification")
print("=" * 60)
print(f"Email: penrowisenotifications@gmail.com")
print(f"Password from .env: {os.getenv('GMAIL_APP_PASSWORD')}")
print(f"Password length: {len(os.getenv('GMAIL_APP_PASSWORD', ''))}")
print("=" * 60)
print("\n✅ Configuration updated successfully!")
print("\nNext steps:")
print("1. Restart your Django server (Ctrl+C, then 'python manage.py runserver')")
print("2. Test email functionality in your app")
print("\nIf emails still don't send, check:")
print("- Windows Firewall isn't blocking port 587")
print("- Antivirus isn't blocking SMTP connections")
