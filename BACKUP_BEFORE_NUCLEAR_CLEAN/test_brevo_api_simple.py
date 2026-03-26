"""
Simple Brevo API test without Django.
Tests the API directly to verify credentials work.
"""

import os
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Load environment variables
load_dotenv()

print("=" * 60)
print("BREVO API SIMPLE TEST")
print("=" * 60)

# Get API key
api_key = os.getenv('BREVO_API_KEY')

if not api_key:
    print("❌ BREVO_API_KEY not found in .env file!")
    exit(1)

print(f"\n✅ API Key found: {api_key[:20]}...")

# Configure API
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = api_key

# Create API instance
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

# Get test email
test_email = input("\nEnter your email address to receive a test: ").strip()

if not test_email:
    print("❌ No email provided. Exiting.")
    exit(1)

print(f"\n📧 Sending test email to: {test_email}")
print("Please wait...")

# Create email
sender = sib_api_v3_sdk.SendSmtpEmailSender(
    name="PENRO WSTI Notifications",
    email="penrowisenotifications@gmail.com"
)

to = [sib_api_v3_sdk.SendSmtpEmailTo(email=test_email)]

send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
    sender=sender,
    to=to,
    subject="✅ Brevo API Test - PENRO WSTI",
    text_content="This is a test email sent via Brevo API. If you receive this, the API is working!",
    html_content="""
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
    """
)

try:
    # Send email
    api_response = api_instance.send_transac_email(send_smtp_email)
    
    print("\n" + "=" * 60)
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print("=" * 60)
    print(f"Message ID: {api_response.message_id}")
    print(f"Recipient: {test_email}")
    print("\nCheck your inbox (and spam folder)")
    print("=" * 60)
    
except ApiException as e:
    print("\n" + "=" * 60)
    print("❌ EMAIL FAILED!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check if BREVO_API_KEY is correct in .env")
    print("2. Verify sender email is verified in Brevo dashboard")
    print("3. Check Brevo account status")
    print("=" * 60)

except Exception as e:
    print("\n" + "=" * 60)
    print("❌ UNEXPECTED ERROR!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("=" * 60)
