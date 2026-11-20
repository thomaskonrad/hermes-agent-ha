#!/usr/bin/env python3
"""Create the upstream-sync GitHub App from its manifest (one browser click).

Flow (GitHub App manifest flow):
  1. This script serves a page that POSTs scripts/app-manifest.json to GitHub.
  2. You click "Create GitHub App" once on GitHub.
  3. GitHub redirects to http://localhost:8765/callback?code=...
  4. This script exchanges the code (POST /app-manifests/{code}/conversions)
     for the App ID and private key.

The private key is written to ~/.config/hermes-agent-ha/upstream-sync-app.pem
with mode 0600. It is never printed or written inside the repository.
"""

from __future__ import annotations

import html
import http.server
import json
import os
import pathlib
import subprocess
import sys
import threading
import urllib.parse
import webbrowser

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "app-manifest.json"
KEY_DIR = pathlib.Path.home() / ".config" / "hermes-agent-ha"
KEY_PATH = KEY_DIR / "upstream-sync-app.pem"
ID_PATH = KEY_DIR / "upstream-sync-app-id.txt"
PORT = 8765
ORG_OR_USER_URL = "https://github.com/settings/apps/new"
state = {"code": None}


def _page() -> bytes:
    manifest = html.escape(MANIFEST.read_text(encoding="utf-8"), quote=True)
    body = f"""<!doctype html><meta charset="utf-8"><title>Create GitHub App</title>
<p>Click the button once to create the GitHub App from the manifest.</p>
<form action="{ORG_OR_USER_URL}" method="post">
<input type="hidden" name="manifest" value="{manifest}">
<button type="submit">Create GitHub App</button>
</form>"""
    return body.encode("utf-8")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._send(200, _page())
        elif parsed.path == "/callback":
            qs = urllib.parse.parse_qs(parsed.query)
            state["code"] = (qs.get("code") or [None])[0]
            self._send(200, b"Received. You can close this tab.")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self._send(404, b"not found")

    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the code out of logs
        return


def exchange(code: str) -> dict:
    """Exchange the one-time code. Uses the gh CLI's auth-free POST endpoint."""
    out = subprocess.run(
        ["gh", "api", "-X", "POST", f"/app-manifests/{code}/conversions"],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def main() -> int:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(KEY_DIR, 0o700)
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Opening http://localhost:{PORT}/ - click 'Create GitHub App' once.", file=sys.stderr)
    webbrowser.open(f"http://localhost:{PORT}/")
    server.serve_forever(poll_interval=0.5)
    server.server_close()

    code = state["code"]
    if not code:
        print("No code received; nothing was created.", file=sys.stderr)
        return 1
    app = exchange(code)
    app_id = app.get("id")
    pem = app.get("pem")
    if not app_id or not pem:
        print("The exchange response had no id or pem; nothing was stored.", file=sys.stderr)
        return 1
    fd = os.open(KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(pem)
    os.chmod(KEY_PATH, 0o600)
    ID_PATH.write_text(f"{app_id}\n", encoding="utf-8")
    print(f"App created: slug={app.get('slug')} id={app_id}")
    print(f"Private key stored at {KEY_PATH} (mode 0600, not in the repository).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
