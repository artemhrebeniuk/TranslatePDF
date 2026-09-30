import sys
import os

# Add root directory to python search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        # If Vercel rewrote PATH_INFO to internal function path, recover original requested path
        if path in ("/api/index", "/api/index.py", "/api", ""):
            orig = (
                environ.get("HTTP_X_FORWARDED_URI")
                or environ.get("HTTP_X_MATCHED_PATH")
                or environ.get("RAW_URI")
            )
            if orig:
                clean_path = orig.split("?")[0]
                if clean_path and clean_path not in ("/api/index", "/api/index.py"):
                    environ["PATH_INFO"] = clean_path

        return self.wsgi_app(environ, start_response)

flask_app.wsgi_app = VercelWSGIMiddleware(flask_app.wsgi_app)

# Vercel entrypoint
app = flask_app
