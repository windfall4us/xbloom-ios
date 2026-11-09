#!/usr/bin/env python3
"""iOS bundle E2E harness: serve ios/web statically, proxy GET-only to production,
and inject the Capacitor mock + same-origin server URL into index.html.

Why the injection: on a real device absURL() points at the configured server and
WKWebView is not subject to CORS. In a desktop browser the shell is served from
127.0.0.1 while the API lives on 192.168.50.22:8088, so every call would be a
blocked cross-origin request. Pointing the shell at the proxy origin keeps the
bundle unmodified and still exercises the real payloads.
Non-GET is refused with 405 so the test cannot mutate production.
"""
import http.server, socketserver, urllib.request, urllib.error, sys

ROOT = "/home/windfall/coffee/ios/web"
UPSTREAM = "http://192.168.50.22:8088"
PORT = 8098
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
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), H) as s:
        print(f"serving {ROOT} on :{PORT} (GET-only proxy -> {UPSTREAM})", flush=True)
        s.serve_forever()
