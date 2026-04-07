"""
Simple Brevo API test without Django.
Tests the API directly using env-based configuration.
"""

import os

from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


load_dotenv()

api_key = os.getenv("BREVO_API_KEY")
default_from_email = os.getenv("EMAIL_HOST_USER") or os.getenv("DEFAULT_FROM_EMAIL", "")

if not api_key or not default_from_email:
    raise SystemExit(1)

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = api_key
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

test_email = input("\nEnter your email address to receive a test: ").strip()
sender = sib_api_v3_sdk.SendSmtpEmailSender(
    name="PENRO WSTI Notifications",
    email=default_from_email,
)
to = [sib_api_v3_sdk.SendSmtpEmailTo(email=test_email)]
send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
    sender=sender,
    to=to,
    subject="Brevo API Test - PENRO WSTI",
    text_content="This is a test email sent via Brevo API.",
)

try:
    api_instance.send_transac_email(send_smtp_email)
except ApiException as error:
    print(error)
    raise SystemExit(1)
