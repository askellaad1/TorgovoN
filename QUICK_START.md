# Quick Start Guide

## Prerequisites
- Python 3.8+
- PostgreSQL
- Redis
- Node.js 18+ (for frontend)

## Setup Instructions

### 1. Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Copy environment file
cp .env.example .env

# Edit .env file with your settings
# Make sure to set DJANGO_SECRET_KEY, database credentials, etc.
```

### 3. Database Setup
```bash
# Create PostgreSQL database
createdb torgovo_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
# Start Django development server
python manage.py runserver

# In another terminal, start Celery worker
celery -A TorgovoN worker --loglevel=info

# In another terminal, start Celery beat
celery -A TorgovoN beat --loglevel=info
```

### 5. Frontend Setup (Optional)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Troubleshooting

### If you get import errors:
1. Make sure all apps have `__init__.py` files
2. Check that all requirements are installed
3. Verify database connection in `.env` file

### Common Issues:
- **Database connection failed**: Check PostgreSQL is running and credentials are correct
- **Redis connection failed**: Make sure Redis server is running
- **Import errors**: Run `python manage.py check` to diagnose issues

## API Documentation
Once the server is running, visit:
- Admin interface: http://localhost:8000/admin/
- API endpoints: http://localhost:8000/api/v1/

## Production Deployment
Use Docker for production deployment:
```bash
docker-compose up -d
```