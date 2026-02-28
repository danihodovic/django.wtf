"""Gunicorn configuration file.

Can be overridden by environment variables.
https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os

# Bind
port = os.getenv("PORT", "80")
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")

# Workers
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_tmp_dir = "/dev/shm"

# Preload application - load app code before forking workers
# Shares code memory across all workers (saves memory via copy-on-write)
preload_app = os.getenv("GUNICORN_PRELOAD", "true").lower() in ("true", "1", "yes")

# Restart workers after N requests (prevents memory leaks)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "10000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", "90"))

# Logging (access logs disabled - use Django/ingress logs)
accesslog = None
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
