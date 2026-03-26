"""
Test if .env is being loaded correctly
"""
import os
import sys

# Clear any cached environment variables
if 'GMAIL_APP_PASSWORD' in os.environ:
    del os.environ['GMAIL_APP_PASSWORD']

# Force reload dotenv
from dotenv import load_dotenv
load_dotenv(override=True)

password = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 60)
print("ENVIRONMENT VARIABLE TEST")
print("=" * 60)
print(f"Password loaded: {'YES' if password else 'NO'}")
print(f"Password length: {len(password) if password else 0}")
print(f"Password value: {password}")
print(f"Expected: bdyjcnbxnyhumyrx")
print(f"Match: {'YES' if password == 'bdyjcnbxnyhumyrx' else 'NO'}")
print("=" * 60)

# Also check the .env file directly
print("\nReading .env file directly:")
with open('.env', 'r') as f:
    for line in f:
        if 'GMAIL_APP_PASSWORD' in line and not line.strip().startswith('#'):
            print(f"Found in file: {line.strip()}")
