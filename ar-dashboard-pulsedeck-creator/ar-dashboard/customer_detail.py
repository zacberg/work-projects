#!/usr/bin/env python3
"""
customer_detail.py <entity_id> — LIVE per-customer drill-down for the dashboard.

Queries NetSuite (production, live) for the account's open invoices and Salesforce
(production, live) for its hold/flags, and prints JSON. Called on-demand by the
dashboard's /api/customer endpoint when a user clicks an account — so it always
reflects the live source systems, not the cached snapshot.

    python customer_detail.py 12345
"""
import sys, json, re
import ns_client

NS_PREFIX_RE = re.compile(r"^\d+ADV\s+", re.I)


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def clean_name(n):
    return NS_PREFIX_RE.sub("", str(n or "")).split(" (")[0].strip()


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(json.dumps({"error": "numeric entity id required"}))
        return
    eid = int(sys.argv[1])

    # ── NetSuite: live open invoices for this customer ──
    rows = ns_client.suiteql(
        "SELECT tranid, BUILTIN.DF(entity) AS customer, BUILTIN.DF(currency) AS cur, "
        "foreignamountunpaid, foreignamountunpaid*exchangerate AS usd, "
        "TO_CHAR(trandate,'YYYY-MM-DD') AS trandate, TO_CHAR(duedate,'YYYY-MM-DD') AS duedate, "
        "daysoverduesearch AS dpd "
        f"FROM Transaction WHERE type='CustInvc' AND status='A' AND entity={eid} AND foreignamountunpaid <> 0 "
        "ORDER BY daysoverduesearch DESC")
    invoices = [{
        "invoice": r.get("tranid"),
        "currency": r.get("cur"),
        "amount_native": round(_f(r.get("foreignamountunpaid")), 2),
        "amount_usd": round(_f(r.get("usd")), 2),
        "invoice_date": r.get("trandate"),
        "due_date": r.get("duedate"),
        "dpd": int(_f(r.get("dpd"))),
    } for r in rows]
    name = clean_name(rows[0].get("customer")) if rows else f"Entity {eid}"
    total_usd = round(sum(i["amount_usd"] for i in invoices), 2)
    max_dpd = max((i["dpd"] for i in invoices), default=0)

    # ── Salesforce: live flags for this account (best-effort name match) ──
    sf = None
    try:
        import sf_client
        fields = ["Support_Hold__c", "Account_Litigation_Hold__c", "Bankruptcy_Hold__c",
                  "Stop_Hold_Override__c", "Strategic_Account__c", "Strategic_Account_Child__c",
                  "Possible_Pending_Hold__c", "X3rd_Party_Collections__c", "Collections_Rep__c"]
        key = name.replace("'", "\\'")[:20]
        recs = sf_client.soql(
            "SELECT Name, Owner.Name, " + ", ".join(fields) +
            f" FROM Account WHERE Name LIKE '%{key}%' LIMIT 5")
        if recs:
            r = recs[0]
            owner = r.get("Owner") or {}
            sf = {"name": r.get("Name"), "owner": owner.get("Name", "") if isinstance(owner, dict) else "",
                  "rep": r.get("Collections_Rep__c", "")}
            sf["holds"] = [f.replace("__c", "").replace("X3rd", "3rd").replace("_", " ")
                           for f in fields if r.get(f) is True]
    except Exception as e:
        sf = {"error": str(e)[:80]}

    print(json.dumps({
        "entity": eid, "name": name, "total_usd": total_usd,
        "max_dpd": max_dpd, "invoice_count": len(invoices),
        "invoices": invoices, "salesforce": sf,
        "_live": True,
    }))


if __name__ == "__main__":
    main()
