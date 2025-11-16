import time
from django.core.cache import cache
from django.http import JsonResponse


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = 100  # requests per minute
        self.window = 60

    def __call__(self, request):
        ip = self.get_client_ip(request)
        key = f"rate_limit:{ip}"

        request_count = cache.get(key, 0)

        if request_count >= self.rate_limit:
            return JsonResponse(
                {"error": "Rate limit exceeded. Try again later."},
                status=429
            )

        cache.set(key, request_count + 1, self.window)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')