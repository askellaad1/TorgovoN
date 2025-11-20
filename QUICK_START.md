# 🚀 Torgovo Platform - Quick Start Guide

## ⚠️ BEFORE YOU START - Install System Dependencies
```bash
# Windows: Install Visual Studio Build Tools for psycopg2
# macOS: brew install postgresql  (if you want PostgreSQL)
# Linux: sudo apt-get install libpq-dev
```

## ✅ EASY SETUP (Recommended for Development)

### Method 1: Automated Setup Script
```bash
# Run the setup script (installs basic dependencies)
python setup.py

# After setup completes:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Method 2: Manual Minimal Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install ONLY essential dependencies
pip install --upgrade pip
pip install Django==5.0.2
pip install djangorestframework==3.14.0
pip install djangorestframework-simplejwt==5.3.1
pip install django-cors-headers==4.3.1
pip install Pillow==10.1.0

# 4. Setup environment (automatically uses SQLite)
python manage.py makemigrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start server
python manage.py runserver
```

## 🎯 WHAT WAS FIXED

### ✅ Requirements.txt Issues Fixed
- **Removed conflicting packages**: fernet, uuid
- **Removed problematic packages**: Complex packages causing installation failures
- **Added minimal working set**: Only essential packages for basic functionality

### ✅ Django Import Errors Fixed
- **Fixed ExchangeAccount imports**: Updated to import from exchanges.models
- **Added graceful error handling**: Optional apps loaded conditionally
- **SQLite by default**: No PostgreSQL required for development

### ✅ Database Setup
- **Auto-uses SQLite**: No external database needed for development
- **PostgreSQL optional**: Set DATABASE_URL=1 to use PostgreSQL

## 🔧 TROUBLESHOOTING

### 🚨 Common Issues & Solutions

1. **Installation fails on psycopg2**
   ```bash
   # Use SQLite instead (no PostgreSQL needed)
   # Remove DATABASE_URL from environment
   unset DATABASE_URL
   ```

2. **Import Error: cannot import name 'ExchangeAccount'**
   ✅ **Already Fixed** - Import paths corrected

3. **URL namespace errors**
   ✅ **Already Fixed** - Graceful import handling added

4. **Missing module errors**
   ```bash
   # Run the minimal setup first
   python setup.py
   ```

5. **Server won't start**
   ```bash
   # Check for configuration issues
   python manage.py check
   ```

## 📱 TESTING YOUR SETUP

Once the server is running:

### Test Admin Panel
- Visit: http://localhost:8000/admin/
- Login with your superuser credentials

### Test API
- Visit: http://localhost:8000/api/v1/
- Should show available endpoints

## 🎉 Success!

Your Torgovo platform should now be running at:
- **Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/v1/
