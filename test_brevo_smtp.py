"""
Test Brevo SMTP connection
"""
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Force reload
load_dotenv(override=True)

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

print("=" * 70)
print("Brevo SMTP Connection Test")
print("=" * 70)
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print(f"Username: {EMAIL_HOST_USER}")
print(f"Password: {EMAIL_HOST_PASSWORD[:20]}...{EMAIL_HOST_PASSWORD[-10:]}")
print("=" * 70)

if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("\n❌ ERROR: Email credentials not found in .env file")
    exit(1)

try:
    print("\n🔄 Connecting to Brevo SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    
    print("🔄 Starting TLS...")
    server.starttls()
    
    print("🔄 Attempting login...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("\n✅ SUCCESS! Brevo SMTP connection successful!")
    print("✅ Your credentials are correct and working.")
    print("✅ Email notifications will work properly.")
    print("\n📊 Brevo Free Tier: 300 emails/day")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print("\n📋 Troubleshooting:")
    print("1. Verify your SMTP key is correct")
    print("2. Check that your sender email is verified in Brevo")
    print("3. Generate a new SMTP key if needed")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"Error: {e}")
    print("\nCheck your internet connection and firewall settings.")

print("\n" + "=" * 70)
