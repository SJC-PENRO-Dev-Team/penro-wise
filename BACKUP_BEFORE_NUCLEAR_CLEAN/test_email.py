"""
Test Gmail SMTP Connection
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

print("=" * 50)
print("Testing Gmail SMTP Connection")
print("=" * 50)
print(f"Email: {EMAIL_HOST_USER}")
print(f"Password length: {len(EMAIL_HOST_PASSWORD) if EMAIL_HOST_PASSWORD else 0}")
print(f"Password (masked): {'*' * len(EMAIL_HOST_PASSWORD) if EMAIL_HOST_PASSWORD else 'NOT SET'}")
print("=" * 50)

try:
    # Create SMTP connection
    print("\n1. Connecting to Gmail SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    
    print("2. Starting TLS encryption...")
    server.starttls()
    
    print("3. Logging in...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("4. Creating test email...")
    msg = MIMEText("This is a test email from PENRO WSTI System")
    msg['Subject'] = "Test Email - PENRO WSTI"
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = EMAIL_HOST_USER  # Send to self
    
    print("5. Sending email...")
    server.send_message(msg)
    
    print("6. Closing connection...")
    server.quit()
    
    print("\n" + "=" * 50)
    print("✅ SUCCESS! Email sent successfully!")
    print("=" * 50)
    
except smtplib.SMTPAuthenticationError as e:
    print("\n" + "=" * 50)
    print("❌ AUTHENTICATION ERROR!")
    print("=" * 50)
    print(f"Error: {e}")
    print("\nPossible causes:")
    print("1. App Password is incorrect")
    print("2. 2-Step Verification is not enabled on Gmail account")
    print("3. App Password was revoked")
    print("\nSolution:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Generate a new App Password")
    print("3. Update GMAIL_APP_PASSWORD in .env file")
    
except Exception as e:
    print("\n" + "=" * 50)
    print("❌ ERROR!")
    print("=" * 50)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
