"""
Test Brevo SMTP connectivity on different ports.
Run this on Render to see which port works.
"""

import socket
import os
from dotenv import load_dotenv

load_dotenv()

BREVO_HOST = "smtp-relay.brevo.com"
PORTS = [25, 465, 587, 2525]

print("=" * 60)
print("BREVO SMTP PORT CONNECTIVITY TEST")
print("=" * 60)

for port in PORTS:
    print(f"\nTesting port {port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((BREVO_HOST, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port}: OPEN - Connection successful!")
        else:
            print(f"❌ Port {port}: CLOSED - Connection failed (error code: {result})")
    except socket.timeout:
        print(f"❌ Port {port}: TIMEOUT - Connection timed out after 10 seconds")
    except Exception as e:
        print(f"❌ Port {port}: ERROR - {str(e)}")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("Use the port that shows '✅ OPEN' in your EMAIL_PORT setting")
print("=" * 60)
