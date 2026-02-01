"""
Production WSGI Entry Point for SecureAttend Pro
Use this with Gunicorn: gunicorn wsgi:application
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')

# Import app
from app import app, socketio

# Export application for WSGI server
application = app

# For SocketIO support with Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
