"""
ns_client.py — NetSuite SuiteQL client (Token-Based Auth / OAuth 1.0a HMAC-SHA256).

Reads credentials from .env. Use suiteql(query) to run a SuiteQL statement and
get back all rows (handles pagination automatically).

    from ns_client import suiteql
    rows = suiteql("SELECT id, entityid FROM customer FETCH FIRST 5 ROWS ONLY")
"""
import os
import requests
from requests_oauthlib import OAuth1
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA256
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

ACCOUNT = os.environ["NS_ACCOUNT_ID"]                 # e.g. 8151367_SB1
HOST = ACCOUNT.lower().replace("_", "-")              # 8151367-sb1
BASE_URL = f"https://{HOST}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"


def _auth():
    return OAuth1(
        client_key=os.environ["NS_CONSUMER_KEY"],
        client_secret=os.environ["NS_CONSUMER_SECRET"],
        resource_owner_key=os.environ["NS_TOKEN_ID"],
        resource_owner_secret=os.environ["NS_TOKEN_SECRET"],
        signature_method=SIGNATURE_HMAC_SHA256,
        realm=ACCOUNT,
    )


def suiteql(query, page_size=1000, max_pages=50):
    """Run a SuiteQL query, following pagination. Returns a list of row dicts."""
    auth = _auth()
    headers = {"Prefer": "transient", "Content-Type": "application/json"}
    rows, offset, pages = [], 0, 0
    while pages < max_pages:
        url = f"{BASE_URL}?limit={page_size}&offset={offset}"
        resp = requests.post(url, auth=auth, headers=headers, json={"q": query}, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"SuiteQL {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        rows.extend(data.get("items", []))
        if not data.get("hasMore"):
            break
        offset += page_size
        pages += 1
    return rows


if __name__ == "__main__":
    # connectivity test
    print(f"Account: {ACCOUNT}  Host: {HOST}")
    try:
        r = suiteql("SELECT id, companyname, entityid FROM customer FETCH FIRST 3 ROWS ONLY")
        print(f"[OK] connected. sample rows: {len(r)}")
        for row in r:
            print("   ", row)
    except Exception as e:
        print(f"[FAIL] {e}")
