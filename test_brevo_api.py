"""
Test Brevo API email sending.
Run this to verify the API works before deploying.

Usage: python test_brevo_api.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from notifications.services.email_service import send_logged_email

print("=" * 60)
print("BREVO API EMAIL TEST")
print("=" * 60)

# Test email
test_email = input("\nEnter your email address to receive a test email: ").strip()

if not test_email:
    print("❌ No email provided. Exiting.")
    exit(1)

print(f"\n📧 Sending test email to: {test_email}")
print("Please wait...")

try:
    email_log = send_logged_email(
        recipient_email=test_email,
        subject="Test Email from PENRO WSTI (Brevo API)",
        body_text="This is a test email sent via Brevo API. If you receive this, the API is working correctly!",
        body_html="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1e3a5f;">✅ Brevo API Test Successful!</h2>
            <p>This is a test email sent via <strong>Brevo API</strong> (not SMTP).</p>
            <p>If you receive this email, it means:</p>
            <ul>
                <li>✅ Brevo API is configured correctly</li>
                <li>✅ API key is valid</li>
                <li>✅ Emails will work on Render</li>
            </ul>
            <p style="color: #64748b; font-size: 12px; margin-top: 20px;">
                Sent from PENRO WSTI System
            </p>
        </body>
        </html>
        """,
        email_type="test",
        fail_silently=False
    )
    
    print("\n" + "=" * 60)
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print("=" * 60)
    print(f"Status: {email_log.status}")
    print(f"Sent at: {email_log.sent_at}")
    print(f"\nCheck your inbox at: {test_email}")
    print("(Check spam folder if you don't see it)")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ EMAIL FAILED!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check if BREVO_API_KEY is set in .env")
    print("2. Verify the API key is correct")
    print("3. Check if the sender email is verified in Brevo")
    print("=" * 60)
