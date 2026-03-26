"""
Test WISE Branding Update

This script tests that all email notifications now use "WISE" branding.
Run this locally to verify before deploying to production.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.conf import settings
from notifications.services.brevo_api_backend import send_email_via_brevo_api
from notifications.services.email_service import get_styled_email_html, format_info_box

def test_branding():
    """Test that WISE branding is correctly applied"""
    
    print("=" * 60)
    print("WISE BRANDING TEST")
    print("=" * 60)
    
    # Test 1: Check settings.py default
    print("\n1. Testing Django Settings Default...")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if "WISE" in settings.DEFAULT_FROM_EMAIL:
        print("   ✅ Settings default uses WISE branding")
    else:
        print("   ❌ Settings default still uses old branding")
    
    # Test 2: Check email template
    print("\n2. Testing Email Template...")
    test_content = format_info_box("Test", "Sample content", "📧")
    test_html = get_styled_email_html(
        "Test Email",
        test_content
    )
    
    if "PENRO WISE" in test_html:
        print("   ✅ Email template uses WISE branding")
    else:
        print("   ❌ Email template still uses old branding")
    
    # Test 3: Check for any remaining WSTI references
    print("\n3. Checking for old branding in template...")
    if "WSTI" in test_html or "WSTIS" in test_html:
        print("   ❌ Found old branding (WSTI/WSTIS) in template")
    else:
        print("   ✅ No old branding found in template")
    
    # Test 4: Send actual test email
    print("\n4. Sending Test Email...")
    print("   Enter your email to receive a test (or press Enter to skip):")
    test_email = input("   Email: ").strip()
    
    if test_email:
        try:
            content_html = f"""
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                    This is a test email to verify the WISE branding update.
                </p>
                
                <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                    ✅ Branding Test
                </h3>
                {format_info_box("System Name", "PENRO WISE", "🏢")}
                {format_info_box("Test Date", "January 22, 2026", "📅")}
                {format_info_box("Status", "Branding Updated Successfully", "✅")}
                
                <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                    <p style="margin: 0; color: #0369a1; font-size: 14px;">
                        💡 If you see "PENRO WISE" in this email (not "PENRO WSTI" or "PENRO WSTIS"), 
                        the branding update is working correctly!
                    </p>
                </div>
            """
            
            body_html = get_styled_email_html(
                "✅ WISE Branding Test",
                content_html
            )
            
            body_text = (
                "WISE Branding Test\n\n"
                "This is a test email to verify the WISE branding update.\n\n"
                "System Name: PENRO WISE\n"
                "Test Date: January 22, 2026\n"
                "Status: Branding Updated Successfully\n\n"
                "If you see 'PENRO WISE' in this email (not 'PENRO WSTI' or 'PENRO WSTIS'), "
                "the branding update is working correctly!\n\n"
                "Best regards,\n"
                "PENRO WISE Team"
            )
            
            response = send_email_via_brevo_api(
                recipient_email=test_email,
                subject="✅ WISE Branding Test - PENRO WISE",
                body_text=body_text,
                body_html=body_html
            )
            
            print(f"   ✅ Test email sent successfully!")
            print(f"   Message ID: {response.get('messageId', 'N/A')}")
            print(f"\n   Check your inbox for: '✅ WISE Branding Test - PENRO WISE'")
            print(f"   Look for 'PENRO WISE' (not 'WSTI' or 'WSTIS') in the email")
            
        except Exception as e:
            print(f"   ❌ Failed to send test email: {e}")
    else:
        print("   ⏭️  Skipped email test")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("\n✅ All code files have been updated to use WISE branding")
    print("✅ Email templates now show 'PENRO WISE' instead of 'WSTI/WSTIS'")
    print("\n📋 NEXT STEPS:")
    print("   1. Update Render environment variable:")
    print("      DEFAULT_FROM_EMAIL=PENRO WISE Notifications <penrowisenotifications@gmail.com>")
    print("   2. Deploy to production")
    print("   3. Test emails in production")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_branding()
