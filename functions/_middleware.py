from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app

# Configure Flask app for Cloudflare
flask_app.wsgi_app = ProxyFix(
    flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Handle requests
def handle_request(request):
    return flask_app(request.environ, request.start_response)
