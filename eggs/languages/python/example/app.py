import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("SERVER_PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello from Vietnam Hosting Python!\n")

if __name__ == "__main__":
    print(f"Running on 0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
