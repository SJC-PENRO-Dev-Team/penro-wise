"""
Test Gmail SMTP connection with fresh environment reload
"""
import os
import sys

# Clear any cached environment variables
if 'GMAIL_APP_PASSWORD' in os.environ:
    del os.environ['GMAIL_APP_PASSWORD']

from dotenv import load_dotenv
import smtplib

# Force reload of .env file
load_dotenv(override=True)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "notifypenrowstis@gmail.com"
EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 60)
print("Gmail SMTP Connection Test (Fresh)")
print("=" * 60)
print(f"Email: {EMAIL_HOST_USER}")
print(f"Password length: {len(EMAIL_HOST_PASSWORD) if EMAIL_HOST_PASSWORD else 0} characters")
print(f"Password (first 4): {EMAIL_HOST_PASSWORD[:4] if EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"Password (last 4): {EMAIL_HOST_PASSWORD[-4:] if EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print("=" * 60)

if not EMAIL_HOST_PASSWORD:
    print("\n❌ ERROR: GMAIL_APP_PASSWORD not found in .env file")
    sys.exit(1)

try:
    print("\n🔄 Connecting to Gmail SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    
    print("🔄 Starting TLS...")
    server.starttls()
    
    print("🔄 Attempting login...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("\n✅ SUCCESS! Gmail SMTP connection successful!")
    print("✅ Your credentials are correct and working.")
    print("✅ Email notifications will work properly.")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print("\n📋 The app password is incorrect or expired.")
    print("Please generate a new one at: https://myaccount.google.com/apppasswords")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"Error: {e}")

print("\n" + "=" * 60)
