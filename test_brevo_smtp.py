"""
Test Brevo SMTP connection without printing secret values.
"""

import os
import smtplib

from dotenv import load_dotenv


load_dotenv(override=True)

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

print("=" * 70)
print("BREVO SMTP CONNECTION TEST")
print("=" * 70)
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print(f"Username configured: {'YES' if EMAIL_HOST_USER else 'NO'}")
print(f"Password configured: {'YES' if EMAIL_HOST_PASSWORD else 'NO'}")
print("=" * 70)

if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("\nERROR: Email credentials not found in .env")
    raise SystemExit(1)

server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
server.starttls()
server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
server.quit()
print("\nSUCCESS: Brevo SMTP connection completed")
