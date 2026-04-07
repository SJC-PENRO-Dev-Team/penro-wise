"""
Direct test of email credentials from .env without echoing secrets.
"""

import os

from dotenv import load_dotenv


if "EMAIL_HOST_USER" in os.environ:
    del os.environ["EMAIL_HOST_USER"]
if "GMAIL_APP_PASSWORD" in os.environ:
    del os.environ["GMAIL_APP_PASSWORD"]

load_dotenv(override=True)

email = os.getenv("EMAIL_HOST_USER")
password = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 70)
print("EMAIL CREDENTIALS CHECK")
print("=" * 70)
print(f"EMAIL_HOST_USER configured: {'YES' if email else 'NO'}")
print(f"GMAIL_APP_PASSWORD configured: {'YES' if password else 'NO'}")
print(f"Password length: {len(password) if password else 0}")
