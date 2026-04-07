"""
Verify email configuration without exposing secret values.
"""

import os
from dotenv import load_dotenv


load_dotenv(override=True)

email_host_user = os.getenv("EMAIL_HOST_USER", "")
gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

print("=" * 60)
print("EMAIL CONFIGURATION VERIFICATION")
print("=" * 60)
print(f"EMAIL_HOST_USER configured: {'YES' if email_host_user else 'NO'}")
print(f"GMAIL_APP_PASSWORD configured: {'YES' if gmail_password else 'NO'}")
print(f"Password length: {len(gmail_password)}")
print("=" * 60)
print("\nConfiguration check completed.")
print("\nNext steps:")
print("1. Restart your Django server")
print("2. Test email functionality in the app")
