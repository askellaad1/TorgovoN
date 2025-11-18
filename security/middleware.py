"""
Security middleware for Torgovo Platform
Provides rate limiting, request logging, XSS protection, and CORS configuration
"""

import time
import logging
import re
from collections import defaultdict
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('TorgovoN.Security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""

    def process_response(self, request, response):
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Content Type Options
        response['X-Content-Type-Options'] = 'nosniff'

        # Frame Options
        response['X-Frame-Options'] = 'DENY'

        # HSTS (HTTPS required)
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.telegram.org; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware with configurable limits"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = getattr(settings, 'RATE_LIMITS', {
            'default': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'api': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 300},  # 10 requests per 5 minutes
            'webhook': {'requests': 50, 'window': 60},  # 50 webhook triggers per minute
        })

    def _get_client_ip(self, request):
        """Get client IP from request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _get_rate_limit_key(self, request):
        """Generate cache key for rate limiting"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.user, 'id', 'anonymous')

        # Determine rate limit category
        path = request.path
        if path.startswith('/api/'):
            category = 'api'
        elif path.startswith('/webhooks/'):
            category = 'webhook'
        elif path.startswith('/auth/') or path.startswith('/users/'):
            category = 'auth'
        else:
            category = 'default'

        return f"rate_limit:{category}:{user_id}:{client_ip}"

    def process_request(self, request):
        """Check rate limits before processing request"""
        # Skip health checks and admin paths
        if request.path in ['/health/', '/admin/', '/static/']:
            return None

        limit_key = self._get_rate_limit_key(request)
        path = request.path

        # Determine rate limit category
        if path.startswith('/api/'):
            category = 'api'
        elif path.startswith('/webhooks/'):
            category = 'webhook'
        elif path.startswith('/auth/') or path.startswith('/users/'):
            category = 'auth'
        else:
            category = 'default'

        limits = self.rate_limits.get(category, self.rate_limits['default'])
        max_requests = limits['requests']
        window_seconds = limits['window']

        # Get current request count from cache
        current_count = cache.get(limit_key, 0)

        if current_count >= max_requests:
            logger.warning(f"Rate limit exceeded for {limit_key}: {current_count}/{max_requests}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {max_requests} requests per {window_seconds} seconds allowed',
                'retry_after': window_seconds
            }, status=429)

        # Increment counter
        cache.set(limit_key, current_count + 1, window_seconds)

        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Comprehensive request logging for monitoring"""

    def process_request(self, request):
        """Log incoming requests"""
        start_time = time.time()
        request._start_time = start_time

        # Log sensitive endpoints with less detail
        sensitive_patterns = [
            r'/api/v1/users/login',
            r'/api/v1/users/register',
            r'/webhooks/'
        ]

        is_sensitive = any(re.match(pattern, request.path) for pattern in sensitive_patterns)

        if is_sensitive:
            log_data = {
                'method': request.method,
                'path': request.path,
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                'timestamp': start_time,
            }
        else:
            log_data = {
                'method': request.method,
                'path': request.path,
                'ip': self._get_client_ip(request),
                'user_id': getattr(request.user, 'id', 'anonymous'),
                'content_type': request.content_type,
                'content_length': len(request.body) if hasattr(request, 'body') else 0,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                'timestamp': start_time,
            }

        logger.info(f"Request: {log_data}")
        return None

    def process_response(self, request, response):
        """Log response details and timing"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
                'ip': self._get_client_ip(request),
                'user_id': getattr(request.user, 'id', 'anonymous'),
            }

            # Log slow requests (>2 seconds)
            if duration > 2:
                logger.warning(f"Slow request detected: {log_data}")
            else:
                logger.info(f"Response: {log_data}")

        return response

    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Basic SQL injection protection for request parameters"""

    SQL_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bCREATE\b.*\bTABLE\b)",
        r"(\bALTER\b.*\bTABLE\b)",
        r"(\bEXEC\b.*\b\(.*\))",
        r"(\bEXEC\b)",
        r"(--)",
        r"(/\*.*\*/)",
        r"(\bor\b.*\b=\b.*\bor\b)",
        r"(\band\b.*\b=\b.*\band\b)",
    ]

    def process_request(self, request):
        """Check request parameters for SQL injection patterns"""
        suspicious_params = []

        # Check GET parameters
        for key, value in request.GET.items():
            if self._contains_sql_injection(str(value)):
                suspicious_params.append(f"GET:{key}")

        # Check POST parameters
        for key, value in request.POST.items():
            if self._contains_sql_injection(str(value)):
                suspicious_params.append(f"POST:{key}")

        # Check JSON body if present
        if hasattr(request, 'body') and request.content_type == 'application/json':
            try:
                import json
                body_data = json.loads(request.body.decode('utf-8'))
                for key, value in body_data.items():
                    if self._contains_sql_injection(str(value)):
                        suspicious_params.append(f"JSON:{key}")
            except:
                pass

        # Log and block if suspicious patterns found
        if suspicious_params:
            logger.warning(f"SQL injection attempt detected from {self._get_client_ip(request)}. "
                         f"Suspicious parameters: {suspicious_params}")
            return JsonResponse({
                'error': 'Invalid request detected',
                'message': 'Your request contains potentially malicious content'
            }, status=400)

        return None

    def _contains_sql_injection(self, value):
        """Check if value contains SQL injection patterns"""
        value_upper = value.upper()
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False

    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RequestSizeLimitMiddleware(MiddlewareMixin):
    """Limit request size to prevent large payloads"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_upload_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB default
        self.max_body_size = getattr(settings, 'MAX_BODY_SIZE', 1 * 1024 * 1024)  # 1MB default

    def process_request(self, request):
        """Check request size limits"""
        content_length = request.META.get('CONTENT_LENGTH')

        if content_length:
            content_length = int(content_length)

            # Check total body size
            if content_length > self.max_body_size and not request.path.startswith('/admin/'):
                logger.warning(f"Request too large: {content_length} bytes from {self._get_client_ip(request)}")
                return JsonResponse({
                    'error': 'Request too large',
                    'message': f'Maximum request size is {self.max_body_size} bytes'
                }, status=413)

            # Check upload size for file uploads
            if 'multipart/form-data' in request.content_type and content_length > self.max_upload_size:
                logger.warning(f"Upload too large: {content_length} bytes from {self._get_client_ip(request)}")
                return JsonResponse({
                    'error': 'Upload too large',
                    'message': f'Maximum upload size is {self.max_upload_size} bytes'
                }, status=413)

        return None

    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')