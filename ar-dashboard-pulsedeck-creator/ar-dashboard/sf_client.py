"""
sf_client.py — Salesforce SOQL client (OAuth2 client-credentials, sandbox).

Reads SF_CLIENT_ID / SF_CLIENT_SECRET / SF_INSTANCE_URL from .env.

    from sf_client import soql
    rows = soql("SELECT Id, Name FROM Account LIMIT 5")
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

INSTANCE = os.environ["SF_INSTANCE_URL"].rstrip("/")
API_VER = os.environ.get("SF_API_VERSION", "v60.0")

_token = {"access_token": None, "instance_url": INSTANCE}


def _get_token():
    if _token["access_token"]:
        return _token

    refresh = os.environ.get("SF_REFRESH_TOKEN")
    if refresh:
        # Authorization-code flow: trade the stored refresh token for an access token.
        # This is the path that works without an SF admin "Run As" user.
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": os.environ["SF_CLIENT_ID"],
            "client_secret": os.environ["SF_CLIENT_SECRET"],
        }
    else:
        # Fallback: client-credentials (needs admin-enabled Run As user on the app).
        data = {
            "grant_type": "client_credentials",
            "client_id": os.environ["SF_CLIENT_ID"],
            "client_secret": os.environ["SF_CLIENT_SECRET"],
        }

    resp = requests.post(f"{INSTANCE}/services/oauth2/token", data=data, timeout=30)
    if resp.status_code != 200:
        hint = ""
        if not refresh:
            hint = ("  (No SF_REFRESH_TOKEN found — run `python sf_auth.py` to log in "
                    "via the browser, which avoids the admin-only client-credentials user.)")
        raise RuntimeError(f"SF token {resp.status_code}: {resp.text[:400]}{hint}")
    j = resp.json()
    _token["access_token"] = j["access_token"]
    _token["instance_url"] = j.get("instance_url", INSTANCE).rstrip("/")
    return _token


def soql(query):
    """Run a SOQL query, following pagination. Returns list of record dicts."""
    tok = _get_token()
    headers = {"Authorization": f"Bearer {tok['access_token']}"}
    url = f"{tok['instance_url']}/services/data/{API_VER}/query/"
    rows, params = [], {"q": query}
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"SOQL {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
        rows.extend(data.get("records", []))
        nxt = data.get("nextRecordsUrl")
        if not nxt:
            break
        url = f"{tok['instance_url']}{nxt}"
        params = None
    # strip the 'attributes' metadata Salesforce adds to each record
    for r in rows:
        r.pop("attributes", None)
    return rows


if __name__ == "__main__":
    print(f"Instance: {INSTANCE}")
    try:
        r = soql("SELECT Id, Name FROM Account ORDER BY CreatedDate DESC LIMIT 3")
        print(f"[OK] connected. sample rows: {len(r)}")
        for row in r:
            print("   ", row)
    except Exception as e:
        print(f"[FAIL] {e}")
