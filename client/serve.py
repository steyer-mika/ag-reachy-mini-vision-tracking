#!/usr/bin/env python3

import http.server
import socketserver
import os
import sys

# Default port - can be overridden via command line argument
DEFAULT_PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_port() -> int:
    """
    Determine which port to use for the server.

    Priority:
    1. Command line argument (python serve.py 8080)
    2. Default port (3000)
    """
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default {DEFAULT_PORT}")
    return DEFAULT_PORT


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    HTTP request handler with CORS support.

    Adds Access-Control-Allow-Origin header to allow the dashboard
    to connect to WebSocket servers on different ports.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


if __name__ == "__main__":
    port = get_port()

    with socketserver.TCPServer(("", port), HTTPRequestHandler) as httpd:
        print(f"Serving dashboard at http://localhost:{port}")
        print(f"Directory: {DIRECTORY}")
        print(f"Open http://localhost:{port}/index.html in your browser")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped")
