import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = 30
graceful_timeout = 30
keepalive = 5
max_requests = 2000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
capture_output = True
preload_app = False
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")

access_log_format = "%({x-request-id}o)s %(m)s %(s)s %(L)s"
