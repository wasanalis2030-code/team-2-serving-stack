import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/crash":
            os._exit(1)

        if self.path == "/health":
            body = b'{"status":"ok","mode":"chaos-drill"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()