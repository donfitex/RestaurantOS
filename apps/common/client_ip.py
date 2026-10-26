import ipaddress
import os


def client_ip(request):
    """Return the client IP, trusting X-Forwarded-For only behind Render's edge."""
    if os.getenv("RENDER", "").lower() == "true":
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            candidate = forwarded_for.split(",", maxsplit=1)[0].strip()
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                pass
    return request.META.get("REMOTE_ADDR") or "unknown"
