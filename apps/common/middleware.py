import logging
import time
from uuid import uuid4

from django.conf import settings
from django.db import DatabaseError
from django.http import JsonResponse

from .client_ip import client_ip


class SecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid4())
        started = time.perf_counter()
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
                client_ip(request),
                getattr(settings, "AUTH_RATE_LIMIT", 10),
            ):
                response = JsonResponse(
                    {"detail": "Too many authentication attempts. Try again shortly."}, status=429
                )
                response["Retry-After"] = "60"
                response["X-Request-ID"] = request.request_id
                return self.headers(response)
        response = self.headers(self.get_response(request))
        response["X-Request-ID"] = request.request_id
        route = getattr(getattr(request, "resolver_match", None), "route", "unmatched")
        try:
            actor_id = getattr(getattr(request, "user", None), "pk", None)
        except DatabaseError:
            actor_id = None
        logging.getLogger("restaurantos.requests").info(
            "request_completed",
            extra={
                "request_id": request.request_id,
                "method": request.method,
                "route": route,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "user_id": actor_id,
            },
        )
        return response

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
