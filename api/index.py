import sys
import os
import urllib.parse

# Add root directory to python search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query = environ.get("QUERY_STRING", "")
        if "__route__=" in query:
            try:
                params = urllib.parse.parse_qs(query, keep_blank_values=True)
                if "__route__" in params:
                    environ["PATH_INFO"] = params.pop("__route__")[0]
                    environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)
            except Exception:
                pass

        return self.wsgi_app(environ, start_response)

flask_app.wsgi_app = VercelWSGIMiddleware(flask_app.wsgi_app)

# Vercel entrypoint
app = flask_app
