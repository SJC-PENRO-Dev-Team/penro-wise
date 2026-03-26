"""
Brevo API Email Backend

Uses Brevo's HTTP API instead of SMTP to avoid network restrictions on Render.
More reliable than SMTP as it uses HTTPS (port 443) which is rarely blocked.
"""

import os
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoAPIClient:
    """Singleton client for Brevo API"""
    
    _instance = None
    _api_instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize()
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        """Initialize the Brevo API client"""
        api_key = os.getenv('BREVO_API_KEY')
        
        if not api_key:
            raise ValueError(
                "BREVO_API_KEY environment variable is not set! "
                "Please set it in your .env file or Render environment variables."
            )
        
        # Configure API key authorization
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # Create API instance
        cls._api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
        logger.info("Brevo API client initialized successfully")
    
    @classmethod
    def get_api_instance(cls):
        """Get the API instance"""
        if cls._api_instance is None:
            cls._initialize()
        return cls._api_instance


def send_email_via_brevo_api(
    recipient_email,
    subject,
    body_text,
    body_html="",
    from_email=None,
    from_name="PENRO WISE Notifications"
):
    """
    Send email using Brevo API.
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject line
        body_text: Plain text email body
        body_html: HTML email body (optional, recommended)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        from_name: Sender name
    
    Returns:
        dict: Response from Brevo API with message_id
    
    Raises:
        ApiException: If the API call fails
    """
    
    # Get API instance
    api_instance = BrevoAPIClient.get_api_instance()
    
    # Parse from_email if not provided
    if from_email is None:
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        # Extract email from "Name <email@example.com>" format
        if '<' in default_from and '>' in default_from:
            from_name = default_from.split('<')[0].strip()
            from_email = default_from.split('<')[1].split('>')[0].strip()
        else:
            from_email = default_from
    
    # Create sender object
    sender = sib_api_v3_sdk.SendSmtpEmailSender(
        name=from_name,
        email=from_email
    )
    
    # Create recipient object
    to = [sib_api_v3_sdk.SendSmtpEmailTo(email=recipient_email)]
    
    # Create email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,
        to=to,
        subject=subject,
        text_content=body_text,
        html_content=body_html if body_html else None
    )
    
    try:
        # Send email via API
        api_response = api_instance.send_transac_email(send_smtp_email)
        
        logger.info(
            f"✅ Email sent successfully via Brevo API to {recipient_email} "
            f"(message_id: {api_response.message_id})"
        )
        
        return {
            'success': True,
            'message_id': api_response.message_id,
            'recipient': recipient_email
        }
        
    except ApiException as e:
        error_msg = f"Brevo API error: {str(e)}"
        logger.error(f"❌ Failed to send email to {recipient_email}: {error_msg}")
        raise Exception(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"❌ Failed to send email to {recipient_email}: {error_msg}")
        raise Exception(error_msg)
