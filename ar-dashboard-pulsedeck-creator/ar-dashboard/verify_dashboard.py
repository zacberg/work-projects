#!/usr/bin/env python3
"""
verify_dashboard.py — prove the dashboard ties to NetSuite (source of truth).

Re-queries NetSuite LIVE for each headline metric and compares it to what the
dashboard is currently showing (hybrid-snapshot.json). Run anytime:

    python verify_dashboard.py

A PASS on every row means the numbers on the dashboard/deck are a faithful,
current reflection of NetSuite. For an independent finance-grade check, also
compare these to NetSuite's native 'A/R Aging Summary' report (see README note).
"""
import json, os
import ns_client

ADV = "BUILTIN.DF(entity) LIKE '%ADV%'"
HERE = os.path.dirname(os.path.abspath(__file__))


def q1(sql):
    r = ns_client.suiteql(sql)
    return float((r[0] or {}).get("v") or 0) if r else 0.0


def main():
    snap = json.load(open(os.path.join(HERE, "hybrid-snapshot.json"), encoding="utf-8"))
    INV = f"type='CustInvc' AND status='A' AND {ADV}"
    PMT = f"type='CustPymt' AND {ADV}"
    import datetime
    today = datetime.date.today()
    m = today.replace(day=1).isoformat()
    qd = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1).isoformat()

    # (label, dashboard value, live NetSuite value)
    checks = [
        ("Full AR (USD)",
         round(sum(snap["fullAging"].values())),
         round(q1(f"SELECT SUM(foreignamountunpaid*exchangerate) AS v FROM Transaction WHERE {INV}"))),
        (">60 Balance (USD)",
         snap["overdueBalance"]["total"],
         round(q1(f"SELECT SUM(foreignamountunpaid*exchangerate) AS v FROM Transaction WHERE {INV} AND daysoverduesearch>60"))),
        ("Write-off pool >180 (USD)",
         snap["writeOffPool"]["candidateBalance"],
         round(q1(f"SELECT SUM(foreignamountunpaid*exchangerate) AS v FROM Transaction WHERE {INV} AND daysoverduesearch>180"))),
        ("Extreme >365 (USD)",
         snap["extremeDPD"]["balance"],
         round(q1(f"SELECT SUM(foreignamountunpaid*exchangerate) AS v FROM Transaction WHERE {INV} AND daysoverduesearch>365"))),
        ("Cash collected MTD (USD)",
         round(snap["cashCollected"]["mtd"]),
         round(q1(f"SELECT SUM(foreigntotal*exchangerate) AS v FROM Transaction WHERE {PMT} AND trandate>=TO_DATE('{m}','YYYY-MM-DD')"))),
        ("Cash collected QTD (USD)",
         round(snap["cashCollected"]["qtd"]),
         round(q1(f"SELECT SUM(foreigntotal*exchangerate) AS v FROM Transaction WHERE {PMT} AND trandate>=TO_DATE('{qd}','YYYY-MM-DD')"))),
    ]

    print(f"\nDashboard data as of: {snap.get('_generatedAt')}")
    print(f"Sources: {snap.get('_sources')}\n")
    print(f"{'Metric':<28}{'Dashboard':>16}{'NetSuite (live)':>18}  Result")
    print("-" * 78)
    all_ok = True
    for label, dash, live in checks:
        ok = abs(dash - live) <= max(2, round(abs(live) * 0.001))  # within $2 or 0.1%
        all_ok &= ok
        print(f"{label:<28}{dash:>16,}{live:>18,}  {'PASS' if ok else 'DIFF '+format(dash-live,',')}")
    print("-" * 78)
    print("[OK] ALL METRICS TIE TO NETSUITE" if all_ok else "[DIFF] Some rows differ - snapshot may be stale; hit Refresh and re-run.")


if __name__ == "__main__":
    main()
