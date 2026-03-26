"""
Direct test of email credentials from .env
"""
import os
from dotenv import load_dotenv

# Force fresh load
if 'EMAIL_HOST_USER' in os.environ:
    del os.environ['EMAIL_HOST_USER']
if 'GMAIL_APP_PASSWORD' in os.environ:
    del os.environ['GMAIL_APP_PASSWORD']

load_dotenv(override=True)

email = os.getenv('EMAIL_HOST_USER')
password = os.getenv('GMAIL_APP_PASSWORD')

print("=" * 70)
print("EMAIL CREDENTIALS CHECK")
print("=" * 70)
print(f"Email from .env: {email}")
print(f"Password from .env: {password}")
print(f"Password length: {len(password) if password else 0}")
print("=" * 70)

if not email or not password:
    print("\n❌ ERROR: Credentials not found in .env file")
    exit(1)

if len(password) != 16:
    print(f"\n⚠️  WARNING: Gmail app passwords should be 16 characters")
    print(f"   Your password is {len(password)} characters")

print("\n📋 TROUBLESHOOTING:")
print("1. Verify you're using the correct Gmail account:")
print(f"   → {email}")
print("\n2. Generate a NEW app password:")
print("   → Go to: https://myaccount.google.com/apppasswords")
print(f"   → Sign in to: {email}")
print("   → Delete old app passwords")
print("   → Generate new one")
print("   → Copy the 16-character password (remove spaces)")
print("\n3. Update .env file with:")
print(f"   EMAIL_HOST_USER={email}")
print("   GMAIL_APP_PASSWORD=your16charpassword")
print("\n4. Make sure 2-Step Verification is enabled:")
print("   → https://myaccount.google.com/signinoptions/two-step-verification")
