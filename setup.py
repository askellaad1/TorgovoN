#!/usr/bin/env python3
"""
Torgovo Platform Setup Script
This script helps set up the development environment
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"Running: {command}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 Torgovo Platform Setup")
    print("This script will help you set up your development environment")

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)

    print(f"✅ Python version: {sys.version}")

    # Install basic requirements
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install Django==5.0.2", "Installing Django"),
        ("pip install djangorestframework==3.14.0", "Installing DRF"),
        ("pip install djangorestframework-simplejwt==5.3.1", "Installing JWT"),
        ("pip install django-cors-headers==4.3.1", "Installing CORS headers"),
        ("pip install psycopg2-binary==2.9.9", "Installing PostgreSQL adapter"),
        ("pip install celery==5.3.6", "Installing Celery"),
        ("pip install redis==5.0.1", "Installing Redis"),
        ("pip install Pillow==10.1.0", "Installing Pillow"),
        ("pip install python-decouple==3.8", "Installing python-decouple"),
    ]

    failed_commands = []

    for command, description in commands:
        if not run_command(command, description):
            failed_commands.append((command, description))

    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print(f"\n📝 Creating .env file...")
        env_content = """# Django Settings
DJANGO_SECRET_KEY=your-secret-key-change-this-in-production-1234567890
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
# DATABASE_URL=sqlite:///db.sqlite3

# If you want to use PostgreSQL:
# DB_NAME=torgovo_db
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432

# Redis (optional for development)
# REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""

        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

    # Final summary
    print(f"\n{'='*50}")
    print("📋 SETUP SUMMARY")
    print(f"{'='*50}")

    if failed_commands:
        print("⚠️  Some commands failed:")
        for command, description in failed_commands:
            print(f"   - {description}: {command}")
        print("\n💡 You can try installing these packages manually later")
    else:
        print("✅ All packages installed successfully!")

    print("\n🎯 NEXT STEPS:")
    print("1. Create PostgreSQL database (if using PostgreSQL)")
    print("2. Run migrations: python manage.py makemigrations")
    print("3. Run migrations: python manage.py migrate")
    print("4. Create superuser: python manage.py createsuperuser")
    print("5. Start server: python manage.py runserver")

    print("\n📚 Documentation:")
    print("Check QUICK_START.md for detailed instructions")

    print(f"\n{'='*50}")
    print("🎉 Setup completed!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()