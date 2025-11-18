# Multi-stage build for production
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python production stage
FROM python:3.12-slim AS backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=TorgovoN.settings.production

WORKDIR /app

# Install security and system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user early for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser

# Copy and install Python dependencies with better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project with proper permissions
COPY --chown=appuser:appuser . .

# Copy built frontend from builder stage
COPY --from=frontend-builder --chown=appuser:appuser /frontend/dist ./staticfiles/

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/media /app/staticfiles \
    && chown -R appuser:appuser /app/logs /app/media /app/staticfiles

# Switch to non-root user
USER appuser

# Collect static files (will include frontend build)
RUN python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Production Gunicorn config
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gevent", \
     "--worker-connections", "1000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "TorgovoN.wsgi:application"]