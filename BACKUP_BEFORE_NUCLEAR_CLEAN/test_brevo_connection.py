"""
Test Brevo SMTP connection
Run this to verify emails are actually being sent
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print("=" * 60)
    print("BREVO SMTP CONNECTION TEST")
    print("=" * 60)
    
    print(f"\nEmail Configuration:")
    print(f"  HOST: {settings.EMAIL_HOST}")
    print(f"  PORT: {settings.EMAIL_PORT}")
    print(f"  USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  USER: {settings.EMAIL_HOST_USER}")
    print(f"  PASSWORD: {'*' * 20} (hidden)")
    print(f"  FROM: {settings.DEFAULT_FROM_EMAIL}")
    
    # Test email
    test_recipient = input("\nEnter email address to send test to: ")
    
    print(f"\nSending test email to {test_recipient}...")
    
    try:
        result = send_mail(
            subject='Test Email from PENRO System',
            message='This is a test email to verify Brevo SMTP is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_recipient],
            fail_silently=False,
        )
        
        print(f"\n✓ SUCCESS! Email sent successfully.")
        print(f"  Result: {result} email(s) sent")
        print(f"\nCheck your inbox (and spam folder) at: {test_recipient}")
        print("\nIf you don't receive it:")
        print("  1. Check Brevo Dashboard → Statistics → Email")
        print("  2. Look for bounced or blocked emails")
        print("  3. Verify the recipient email is correct")
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to send email")
        print(f"  Error: {str(e)}")
        print(f"\nPossible issues:")
        print("  1. SMTP credentials are incorrect")
        print("  2. Brevo account is not verified")
        print("  3. Network/firewall blocking SMTP")
        print("  4. Brevo service is down")

if __name__ == "__main__":
    test_email()
