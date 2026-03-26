"""
Migrate data from SQLite to PostgreSQL.

This script:
1. Exports data from SQLite (db.sqlite3)
2. Imports data into PostgreSQL

Usage:
    python migrate_sqlite_to_postgres.py
"""

import os
import sys
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
import json

print("=" * 70)
print("SQLITE TO POSTGRESQL DATA MIGRATION")
print("=" * 70)

# Step 1: Export data from SQLite
print("\n1. Exporting data from SQLite...")
print("-" * 70)

# Temporarily use SQLite
os.environ['DATABASE_URL'] = ''  # Clear PostgreSQL URL to use SQLite

# Reload Django settings
from django.conf import settings
from importlib import reload
import penro_project.settings as settings_module
reload(settings_module)

try:
    # Export data to JSON
    with open('sqlite_data.json', 'w', encoding='utf-8') as f:
        call_command('dumpdata', 
                    '--natural-foreign', 
                    '--natural-primary',
                    '--exclude', 'contenttypes',
                    '--exclude', 'auth.permission',
                    '--indent', '2',
                    stdout=f)
    
    print("✅ Data exported to sqlite_data.json")
    
    # Show what was exported
    with open('sqlite_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"\n📊 Exported {len(data)} records")
        
        # Count by model
        model_counts = {}
        for item in data:
            model = item['model']
            model_counts[model] = model_counts.get(model, 0) + 1
        
        print("\nRecords by model:")
        for model, count in sorted(model_counts.items()):
            print(f"   - {model}: {count}")
    
except Exception as e:
    print(f"❌ Export failed: {str(e)}")
    sys.exit(1)

# Step 2: Import data into PostgreSQL
print("\n" + "=" * 70)
print("2. Importing data into PostgreSQL...")
print("-" * 70)

# Set PostgreSQL URL
postgres_url = "postgresql://wisepenrodatabase_user:1FvlotoZSMtyYexsNkNuIby6y8QilX1u@dpg-d5o4bi1r0fns73d0duog-a.oregon-postgres.render.com/wisepenrodatabase"
os.environ['DATABASE_URL'] = postgres_url

# Reload Django settings to use PostgreSQL
reload(settings_module)
from django.core.management import execute_from_command_line

try:
    # Run migrations on PostgreSQL
    print("\nRunning migrations on PostgreSQL...")
    call_command('migrate', '--no-input')
    print("✅ Migrations complete")
    
    # Import data
    print("\nImporting data...")
    with open('sqlite_data.json', 'r', encoding='utf-8') as f:
        call_command('loaddata', 'sqlite_data.json')
    
    print("✅ Data imported successfully!")
    
    # Verify import
    print("\n" + "=" * 70)
    print("3. Verifying data in PostgreSQL...")
    print("-" * 70)
    
    from accounts.models import User, Team, WorkCycle, WorkItem, WorkItemAttachment
    from notifications.models import Notification
    
    print(f"\n✅ Users: {User.objects.count()}")
    print(f"✅ Teams: {Team.objects.count()}")
    print(f"✅ WorkCycles: {WorkCycle.objects.count()}")
    print(f"✅ WorkItems: {WorkItem.objects.count()}")
    print(f"✅ WorkItemAttachments: {WorkItemAttachment.objects.count()}")
    print(f"✅ Notifications: {Notification.objects.count()}")
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print("\nYour data has been successfully migrated from SQLite to PostgreSQL.")
    print("\nNext steps:")
    print("1. Update .env to use PostgreSQL by default")
    print("2. Test your application with PostgreSQL")
    print("3. Deploy to Render")
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"❌ Import failed: {str(e)}")
    print("\nTroubleshooting:")
    print("- Check PostgreSQL connection")
    print("- Verify DATABASE_URL is correct")
    print("- Ensure PostgreSQL database is empty (or use --clear flag)")
    sys.exit(1)
finally:
    # Clean up
    if os.path.exists('sqlite_data.json'):
        print("\n📁 Backup file saved: sqlite_data.json")
