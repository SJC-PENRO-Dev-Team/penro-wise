"""
Test SMTP connection using env-based email configuration.
"""

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD")

print("=" * 50)
print("TESTING SMTP CONNECTION")
print("=" * 50)
print(f"Email configured: {'YES' if EMAIL_HOST_USER else 'NO'}")
print(f"Password configured: {'YES' if EMAIL_HOST_PASSWORD else 'NO'}")
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print("=" * 50)

if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("\nMissing email credentials in .env")
    raise SystemExit(1)

server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
server.starttls()
server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

msg = MIMEText("This is a test email from PENRO WSTI System")
msg["Subject"] = "Test Email - PENRO WSTI"
msg["From"] = EMAIL_HOST_USER
msg["To"] = EMAIL_HOST_USER

server.send_message(msg)
server.quit()
print("\nSUCCESS: Test email sent")
