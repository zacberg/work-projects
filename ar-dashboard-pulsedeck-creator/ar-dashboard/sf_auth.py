"""
sf_auth.py — One-time Salesforce browser login (OAuth2 authorization-code + PKCE).

Why this exists:
  The client-credentials grant is blocked ("no client credentials user enabled")
  because the connected app has no admin-set "Run As" user. The authorization-code
  flow instead lets YOU log in as yourself in the browser — no SF admin needed.

What it does:
  1. Opens your browser to the Salesforce login/approve page.
  2. Captures the ?code= on the local callback (http://localhost:3001/auth/callback).
  3. Exchanges the code for an access token + refresh token.
  4. Writes SF_REFRESH_TOKEN and SF_INSTANCE_URL back into .env.

After this runs once, sf_client.py uses the refresh token automatically (no browser).

    python sf_auth.py
"""
import base64
import hashlib
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")
load_dotenv(ENV_PATH)

CLIENT_ID = os.environ["SF_CLIENT_ID"]
CLIENT_SECRET = os.environ["SF_CLIENT_SECRET"]
BASE = os.environ["SF_INSTANCE_URL"].rstrip("/")
AUTHORIZE_URL = f"{BASE}/services/oauth2/authorize"
TOKEN_URL = f"{BASE}/services/oauth2/token"
REDIRECT_URI = os.environ.get("SF_REDIRECT_URI", "http://localhost:3001/auth/callback")
# api = REST/SOQL access; refresh_token = get a long-lived refresh token
SCOPE = os.environ.get("SF_SCOPE", "api refresh_token")

# PKCE pair
_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")
_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(_verifier.encode()).digest()
).decode().rstrip("=")
_state = secrets.token_urlsafe(16)

_result = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != urllib.parse.urlparse(REDIRECT_URI).path:
            self.send_response(404)
            self.end_headers()
            return
        qs = urllib.parse.parse_qs(parsed.query)
        _result["code"] = qs.get("code", [None])[0]
        _result["state"] = qs.get("state", [None])[0]
        _result["error"] = qs.get("error_description", qs.get("error", [None]))[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ok = _result.get("code") and not _result.get("error")
        msg = ("Salesforce authorized. You can close this tab and return to the terminal."
               if ok else f"Authorization failed: {_result.get('error')}")
        self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px'>"
                         f"<h2>{msg}</h2></body></html>".encode())

    def log_message(self, *args):
        pass  # silence the default request logging


def _update_env(values):
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    keys = set(values)
    out, seen = [], set()
    for line in lines:
        k = line.split("=", 1)[0].strip() if "=" in line else None
        if k in keys:
            out.append(f"{k}={values[k]}")
            seen.add(k)
        else:
            out.append(line)
    for k in keys - seen:
        out.append(f"{k}={values[k]}")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": _state,
        "code_challenge": _challenge,
        "code_challenge_method": "S256",
        "prompt": "login",
    }
    url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    port = urllib.parse.urlparse(REDIRECT_URI).port or 80
    server = HTTPServer(("localhost", port), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    print(f"Opening browser to log in to Salesforce...\nIf it doesn't open, paste this URL:\n{url}\n")
    webbrowser.open(url)
    print(f"Waiting for the callback on {REDIRECT_URI} ...")

    # block until the handler fills _result (up to 10 min)
    deadline = time.time() + 600
    while "code" not in _result and "error" not in _result and time.time() < deadline:
        time.sleep(0.2)
    server.shutdown()
    if "code" not in _result and "error" not in _result:
        print("[FAIL] timed out waiting for browser login (10 min).")
        return

    if _result.get("error") or not _result.get("code"):
        print(f"[FAIL] {_result.get('error') or 'no code returned'}")
        return
    if _result.get("state") != _state:
        print("[FAIL] state mismatch (possible CSRF) — aborting")
        return

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _result["code"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": _verifier,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[FAIL] token exchange {resp.status_code}: {resp.text[:500]}")
        return
    tok = resp.json()
    refresh = tok.get("refresh_token")
    instance = tok.get("instance_url", BASE).rstrip("/")
    if not refresh:
        print("[FAIL] no refresh_token in response — the connected app likely lacks the "
              "'refresh_token'/'offline_access' scope. Response keys: " + ", ".join(tok))
        return

    _update_env({"SF_REFRESH_TOKEN": refresh, "SF_INSTANCE_URL": instance})
    print(f"[OK] Logged in. instance_url={instance}")
    print("     Saved SF_REFRESH_TOKEN to .env. Verifying with sf_client.py...")


if __name__ == "__main__":
    main()
