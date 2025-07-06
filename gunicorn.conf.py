import os

# Bind the application to a specific IP and port
bind = f"0.0.0.0:{os.getenv('APP_PORT', 8000)}"

workers = 1

# Worker class (recommended for FastAPI/ASGI apps)
worker_class = "uvicorn.workers.UvicornWorker"

# Maximum number of requests a worker can handle before being restarted (to prevent memory leaks)
max_requests = 1000

# random variation to the restart threshold for each worker, ensuring that not all workers restart at the exact same time
max_requests_jitter = 50

# Logging
accesslog = "-"  # Standard output for access logs
errorlog = "-"  # Standard output for error logs
loglevel = "info"

# Graceful timeout for worker shutdown
timeout = 180

# Preload the application to reduce memory usage
preload_app = True

# Enable keep-alive connections
keepalive = 180
