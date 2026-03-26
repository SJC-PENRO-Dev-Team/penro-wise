"""
Test Gmail SMTP connection
"""
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "notifypenrowstis@gmail.com"
EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 60)
print("Gmail SMTP Connection Test")
print("=" * 60)
print(f"Email: {EMAIL_HOST_USER}")
print(f"Password length: {len(EMAIL_HOST_PASSWORD) if EMAIL_HOST_PASSWORD else 0} characters")
print(f"Password (masked): {'*' * (len(EMAIL_HOST_PASSWORD) - 4) + EMAIL_HOST_PASSWORD[-4:] if EMAIL_HOST_PASSWORD and len(EMAIL_HOST_PASSWORD) > 4 else 'NOT SET'}")
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print("=" * 60)

if not EMAIL_HOST_PASSWORD:
    print("\n❌ ERROR: GMAIL_APP_PASSWORD not found in .env file")
    exit(1)

try:
    print("\n🔄 Connecting to Gmail SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.set_debuglevel(1)  # Show detailed debug info
    
    print("\n🔄 Starting TLS...")
    server.starttls()
    
    print("\n🔄 Attempting login...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("\n✅ SUCCESS! Gmail SMTP connection successful!")
    print("✅ Your credentials are correct and working.")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print("\n📋 Troubleshooting steps:")
    print("1. Make sure 2-Step Verification is enabled on your Google account")
    print("2. Generate a new App Password at: https://myaccount.google.com/apppasswords")
    print("3. The app password should be 16 characters (no spaces)")
    print("4. Copy the password exactly as shown (without spaces)")
    print("5. Update the .env file with: GMAIL_APP_PASSWORD=your16charpassword")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"Error: {e}")
    print("\nCheck your internet connection and firewall settings.")

print("\n" + "=" * 60)
