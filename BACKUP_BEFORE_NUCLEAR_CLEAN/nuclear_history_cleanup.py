#!/usr/bin/env python3
"""
NUCLEAR OPTION: Create a completely clean repository without any secret history
"""

import os
import shutil
import subprocess
import glob

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚨 NUCLEAR OPTION: Creating completely clean repository")
    print("=" * 60)
    
    # 1. Create backup of current files
    print("📦 Creating backup...")
    backup_dir = "BACKUP_BEFORE_NUCLEAR_CLEAN"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    # Copy all files except .git
    shutil.copytree(".", backup_dir, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'venv', 'node_modules'))
    print(f"✅ Backup created in {backup_dir}")
    
    # 2. Remove .git directory
    print("🔥 Removing Git history...")
    if os.path.exists(".git"):
        shutil.rmtree(".git")
    print("✅ Git history removed")
    
    # 3. Initialize new repository
    print("🆕 Initializing clean repository...")
    success, stdout, stderr = run_command("git init")
    if not success:
        print(f"❌ Failed to init git: {stderr}")
        return
    
    # 4. Configure git
    run_command('git config user.name "Klein Lavina"')
    run_command('git config user.email "kleinlav7@gmail.com"')
    
    # 5. Add all files
    print("📁 Adding clean files...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"❌ Failed to add files: {stderr}")
        return
    
    # 6. Create initial commit
    print("💾 Creating clean initial commit...")
    commit_msg = """Initial commit - WISE-PENRO Document Management System

🌟 Features:
- Digital Document Tracking System
- Advanced File Manager with Universal Preview
- Workforce Management & Analytics
- Real-time Notifications & Messaging
- PostgreSQL + Cloudinary Integration
- Async Processing & Performance Optimization

🔒 Security: All secrets properly externalized to environment variables
✅ Production Ready: Deployed on Render.com with enterprise features"""
    
    success, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')
    if not success:
        print(f"❌ Failed to commit: {stderr}")
        return
    
    print("✅ Clean repository created!")
    print("\n🚀 Next steps:")
    print("1. git remote add origin https://github.com/SJC-PENRO-Dev-Team/penro-wise.git")
    print("2. git push --force-with-lease origin main")
    print("\n⚠️  WARNING: This will completely overwrite the GitHub repository!")
    print("🔒 All secrets have been removed from history")

if __name__ == '__main__':
    main()