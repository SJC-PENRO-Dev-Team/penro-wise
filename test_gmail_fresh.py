"""
Test Gmail SMTP connection with a fresh environment reload.
"""

import os
import smtplib

from dotenv import load_dotenv


if "GMAIL_APP_PASSWORD" in os.environ:
    del os.environ["GMAIL_APP_PASSWORD"]

load_dotenv(override=True)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 60)
print("GMAIL SMTP CONNECTION TEST (FRESH)")
print("=" * 60)
print(f"Email configured: {'YES' if EMAIL_HOST_USER else 'NO'}")
print(f"Password configured: {'YES' if EMAIL_HOST_PASSWORD else 'NO'}")
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print("=" * 60)

if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("\nERROR: GMAIL_APP_PASSWORD not found in .env")
    raise SystemExit(1)

server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
server.starttls()
server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
server.quit()
print("\nSUCCESS: Gmail SMTP connection completed")
