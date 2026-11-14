#!/usr/bin/env python3
"""iOS bundle E2E harness: serve the bundle statically, proxy GET-only to a server,
and inject the Capacitor mock + same-origin server URL into index.html.

Why the injection: on a real device absURL() points at the configured server and
WKWebView is not subject to CORS. In a desktop browser the shell is served from
127.0.0.1 while the API lives elsewhere, so every call would be a blocked
cross-origin request. Pointing the shell at the proxy origin keeps the bundle
unmodified and still exercises the real payloads.

Non-GET is refused with 405 so the test can never mutate the upstream server.

Usage
    python3 ios_e2e_harness.py [--serve DIR] [--upstream URL] [--port N]

    --serve     bundle directory to serve      (default: ../  -> the folder holding index.html)
    --upstream  API server to proxy GET to     (default: http://127.0.0.1:8088)
    --port      listen port                    (default: 8098)

No absolute paths and no baked-in server address: both come from the command line,
so the harness works from any checkout and does not disclose an internal host.
"""
import argparse, http.server, socketserver, urllib.request, urllib.error, sys
from pathlib import Path


def _parse(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--serve', default=str(Path(__file__).resolve().parent.parent),
                    help='bundle directory to serve (default: the parent of this tools/ dir)')
    ap.add_argument('--upstream', default='http://127.0.0.1:8088',
                    help='upstream API base for GET proxying')
    ap.add_argument('--port', type=int, default=8098)
    return ap.parse_args(argv)


ARGS = _parse(sys.argv[1:])
ROOT = str(Path(ARGS.serve).expanduser().resolve())
UPSTREAM = ARGS.upstream.rstrip('/')
PORT = ARGS.port
PREFIXES = ("/api", "/media", "/raw", "/openapi.json")
MOCK = (b"<script>window.Capacitor={isNativePlatform:function(){return true},"
        b"getPlatform:function(){return 'ios'},Plugins:{}};"
        b"try{localStorage.setItem('xbloom_ios_server_url',location.origin)}catch(e){}</script>")


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *a):
        sys.stderr.write("[e2e] " + fmt % a + "\n")

    def do_GET(self):
        if any(self.path.startswith(p) for p in PREFIXES):
            return self._proxy()
        if self.path.split("?")[0] in ("/", "/index.html"):
            body = (open(f"{ROOT}/index.html", "rb").read())
            body = body.replace(b"<head>", b"<head>" + MOCK, 1)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def _proxy(self):
        try:
            req = urllib.request.Request(UPSTREAM + self.path, headers={"User-Agent": "ios-e2e/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read()
                self.send_response(r.status)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/octet-stream"))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            d = e.read()
            self.send_response(e.code)
            self.send_header("Content-Length", str(len(d)))
            self.end_headers()
            self.wfile.write(d)
        except Exception as e:
            m = str(e).encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(m)))
            self.end_headers()
            self.wfile.write(m)

    def _refuse(self):
        self.send_response(405)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":false,"message":"e2e harness is GET-only"}')

    do_POST = do_PUT = do_PATCH = do_DELETE = _refuse


if __name__ == "__main__":
    if not Path(ROOT, 'index.html').is_file():
        sys.exit(f"no index.html under {ROOT}; pass --serve <dir containing index.html>")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), H) as srv:
        print(f"serving {ROOT} on :{PORT} (GET-only proxy -> {UPSTREAM})", flush=True)
        srv.serve_forever()
