"""
Production Configuration for SecureAttend Pro
Gunicorn WSGI Server Configuration
"""

import multiprocessing
import os

# Server socket
bind = os.getenv('BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'eventlet'  # For SocketIO support
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests (memory leak prevention)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'secureattend_pro'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Development
reload = os.getenv('RELOAD', 'false').lower() == 'true'
reload_extra_files = []

# Daemon mode
daemon = False

# SSL (uncomment for HTTPS)
# keyfile = 'certs/key.pem'
# certfile = 'certs/cert.pem'

def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called before reloading the workers."""
    pass

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass
