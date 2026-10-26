from django.conf import settings
from django.http import JsonResponse


class SecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in [
            "/accounts/login/",
            "/accounts/password_reset/",
            "/register/",
            "/api/v1/auth/login/",
            "/api/v1/auth/register/",
        ]:
            from .throttling import consume

            if not consume(
                "authentication",
                request.META.get("REMOTE_ADDR", "unknown"),
                getattr(settings, "AUTH_RATE_LIMIT", 10),
            ):
                response = JsonResponse(
                    {"detail": "Too many authentication attempts. Try again shortly."}, status=429
                )
                response["Retry-After"] = "60"
                return self.headers(response)
        return self.headers(self.get_response(request))

    def headers(self, response):
        response.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
            ),
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["Referrer-Policy"] = "same-origin"
        return response
