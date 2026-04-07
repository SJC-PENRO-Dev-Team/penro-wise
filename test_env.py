"""
Test if .env is being loaded correctly without exposing secret values.
"""

import os

from dotenv import load_dotenv


if "GMAIL_APP_PASSWORD" in os.environ:
    del os.environ["GMAIL_APP_PASSWORD"]

load_dotenv(override=True)

password = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 60)
print("ENVIRONMENT VARIABLE TEST")
print("=" * 60)
print(f"GMAIL_APP_PASSWORD loaded: {'YES' if password else 'NO'}")
print(f"Password length: {len(password) if password else 0}")
print("=" * 60)

print("\nReading .env file directly:")
with open(".env", "r", encoding="utf-8") as env_file:
    for line in env_file:
        if "GMAIL_APP_PASSWORD" in line and not line.strip().startswith("#"):
            print("Found GMAIL_APP_PASSWORD entry in .env")
