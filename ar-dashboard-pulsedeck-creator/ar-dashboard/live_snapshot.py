#!/usr/bin/env python3
"""
live_snapshot.py — build the AR dashboard snapshot from LIVE data.

NetSuite (sandbox) is the primary source, pulled live via SuiteQL (ns_client).
Salesforce supplies hold/legal flags; it's pulled live via sf_client if the
client-credentials flow is enabled, otherwise it falls back to the last saved
flags file so the merge still works.

Run:  python live_snapshot.py
"""
import json, re, os
from collections import defaultdict
from datetime import datetime, timezone, date

import ns_client

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "hybrid-snapshot.json")
# fallback saved SF data (from the earlier MCP pull)
SF_BASE = r"C:\Users\ZachBergman\.claude\projects\C--Users-ZachBergman\0fa1c09c-26c0-421b-8cf9-3e9acb6f3a42\tool-results"
SF_FLAGS_JSON = os.path.join(SF_BASE, "sf_account_flags_compact.json")
SF_REPS_TXT = os.path.join(SF_BASE, "mcp-claude_ai_Advantive_Salesforce-soqlQueryplatform_sobject_reads-1780491428498.txt")

ADV = "BUILTIN.DF(entity) LIKE '%ADV%'"


def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d


# ── NetSuite (live) ───────────────────────────────────────────────────────
def fetch_netsuite():
    print("NetSuite: overdue customers...")
    # Per-customer USD-converted balances at each DPD threshold (foreignamountunpaid is in
    # the invoice currency; *exchangerate converts to USD). total_overdue = the 60+ DPD
    # balance (invoice-level), so headline tiles reflect true "60+ overdue" and match aging.
    overdue = ns_client.suiteql(
        "SELECT sub.entity, BUILTIN.DF(sub.entity) AS entityname, sub.max_dpd, sub.bal_60, sub.bal_180, sub.bal_365, sub.bal_all, sub.inv60 "
        "FROM (SELECT entity, MAX(daysoverduesearch) AS max_dpd, "
        # thresholds use > (not >=) to match the aging-bucket boundaries (31-60 / 61-90 / …)
        "SUM(CASE WHEN daysoverduesearch>60 THEN foreignamountunpaid*exchangerate ELSE 0 END) AS bal_60, "
        "SUM(CASE WHEN daysoverduesearch>180 THEN foreignamountunpaid*exchangerate ELSE 0 END) AS bal_180, "
        "SUM(CASE WHEN daysoverduesearch>365 THEN foreignamountunpaid*exchangerate ELSE 0 END) AS bal_365, "
        "SUM(foreignamountunpaid*exchangerate) AS bal_all, "
        "SUM(CASE WHEN daysoverduesearch>60 THEN 1 ELSE 0 END) AS inv60 "
        f"FROM Transaction WHERE type='CustInvc' AND status='A' AND {ADV} AND daysoverduesearch >= 1 GROUP BY entity) sub "
        "ORDER BY sub.bal_all DESC")
    ns_customers = [{
        "entity": r.get("entity"), "entityname": r.get("entityname", ""),
        "max_dpd": _f(r.get("max_dpd")),
        "total_overdue": _f(r.get("bal_60")),                 # 60+ DPD balance = headline definition
        "bal_all": _f(r.get("bal_all")), "bal_180": _f(r.get("bal_180")), "bal_365": _f(r.get("bal_365")),
        "invoice_count": int(_f(r.get("inv60"))),
    } for r in overdue]
    print(f"  {len(ns_customers)} overdue customers")

    print("NetSuite: rep assignments...")
    reps = ns_client.suiteql(
        "SELECT entity, BUILTIN.DF(custbody_scg_collection_rep) AS rep_name FROM Transaction "
        f"WHERE type='CustInvc' AND status='A' AND {ADV} AND custbody_scg_collection_rep IS NOT NULL")
    counts = defaultdict(lambda: defaultdict(int))
    for r in reps:
        e, rep = r.get("entity"), (r.get("rep_name") or "").strip()
        if e and rep:
            counts[e][rep] += 1
    entity_primary_rep = {e: max(c, key=c.get) for e, c in counts.items()}
    print(f"  {len(entity_primary_rep)} entities with reps")

    print("NetSuite: full AR aging buckets...")
    case = ("CASE WHEN daysoverduesearch IS NULL OR daysoverduesearch <= 0 THEN '0_Current' "
            "WHEN daysoverduesearch <= 30 THEN '1_1-30' WHEN daysoverduesearch <= 60 THEN '2_31-60' "
            "WHEN daysoverduesearch <= 90 THEN '3_61-90' WHEN daysoverduesearch <= 120 THEN '4_91-120' "
            "WHEN daysoverduesearch <= 180 THEN '5_121-180' WHEN daysoverduesearch <= 365 THEN '6_181-365' "
            "ELSE '7_365plus' END")
    ag = ns_client.suiteql(
        f"SELECT {case} AS bucket, SUM(foreignamountunpaid*exchangerate) AS balance FROM Transaction "
        f"WHERE type='CustInvc' AND status='A' AND {ADV} GROUP BY {case}")
    label = {"0_Current": "Current", "1_1-30": "1-30", "2_31-60": "31-60", "3_61-90": "61-90",
             "4_91-120": "91-120", "5_121-180": "121-180", "6_181-365": "181-365", "7_365plus": "365+"}
    full_aging = {label[r["bucket"]]: round(_f(r.get("balance")), 2) for r in ag if r.get("bucket") in label}

    print("NetSuite: cash collected (MTD/QTD + top movers)...")
    today = date.today()
    m_start = today.replace(day=1).isoformat()
    q_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1).isoformat()
    mtd_rows = ns_client.suiteql(
        "SELECT BUILTIN.DF(entity) AS customer, SUM(foreigntotal*exchangerate) AS amt FROM Transaction "
        f"WHERE type='CustPymt' AND {ADV} AND trandate >= TO_DATE('{m_start}','YYYY-MM-DD') "
        "GROUP BY BUILTIN.DF(entity) ORDER BY amt DESC")
    mtd_total = sum(_f(r.get("amt")) for r in mtd_rows)
    qtd_rows = ns_client.suiteql(
        f"SELECT SUM(foreigntotal*exchangerate) AS amt FROM Transaction WHERE type='CustPymt' AND {ADV} "
        f"AND trandate >= TO_DATE('{q_start}','YYYY-MM-DD')")
    qtd_total = _f(qtd_rows[0].get("amt")) if qtd_rows else 0.0

    def clean(n):
        n = re.sub(r"^\d+ADV\s+", "", str(n))
        return n.split(" (")[0].strip()
    cash = {
        "mtd": round(mtd_total, 2), "qtd": round(qtd_total, 2),
        "topMovers": [{"name": clean(r.get("customer")), "amt": round(_f(r.get("amt")), 2)} for r in mtd_rows[:3]],
        "_source": "NetSuite CustPymt (live); may differ from AR Tracker official cash figure",
    }

    print("NetSuite: accounts approaching >60 (30-59 DPD)...")
    appr = ns_client.suiteql(
        "SELECT sub.entity, BUILTIN.DF(sub.entity) AS entityname, sub.max_dpd, sub.total FROM ("
        "SELECT entity, MAX(daysoverduesearch) AS max_dpd, SUM(foreignamountunpaid*exchangerate) AS total FROM Transaction "
        f"WHERE type='CustInvc' AND status='A' AND {ADV} AND daysoverduesearch BETWEEN 30 AND 59 GROUP BY entity) sub "
        "ORDER BY sub.total DESC")
    approaching = [{"name": clean(r.get("entityname")), "balance": round(_f(r.get("total")), 2),
                    "dpd": int(_f(r.get("max_dpd")))} for r in appr[:8]]
    print(f"  {len(approaching)} approaching accounts")
    return ns_customers, entity_primary_rep, full_aging, cash, approaching


# ── Salesforce (live, else saved fallback) ─────────────────────────────────
SF_FIELDS = ["Support_Hold__c", "Account_Litigation_Hold__c", "Bankruptcy_Hold__c", "Stop_Hold_Override__c",
             "Strategic_Account__c", "Strategic_Account_Child__c", "Possible_Pending_Hold__c",
             "X3rd_Party_Collections__c", "Collections_Rep__c"]


def fetch_salesforce():
    try:
        import sf_client
        print("Salesforce: live account flags...")
        soql = ("SELECT Id, Name, Owner.Name, " + ", ".join(SF_FIELDS) +
                " FROM Account WHERE Collections_Rep__c != null OR Support_Hold__c = true")
        recs = sf_client.soql(soql)
        accts = []
        for r in recs:
            owner = r.get("Owner") or {}
            a = {"Id": r.get("Id"), "Name": r.get("Name", ""), "Owner_Name": owner.get("Name", "") if isinstance(owner, dict) else ""}
            for f in SF_FIELDS:
                a[f] = r.get(f)
            accts.append(a)
        rep_names = {p.strip() for a in accts for p in (a.get("Collections_Rep__c") or "").split(";") if p.strip()}
        print(f"  LIVE: {len(accts)} SF accounts")
        return accts, rep_names, "Salesforce production (live)"
    except Exception as e:
        print(f"  SF live unavailable ({str(e)[:80]}); using saved flags")
        with open(SF_FLAGS_JSON, encoding="utf-8") as f:
            accts = json.load(f)
        rep_names = set()
        try:
            reps = json.load(open(SF_REPS_TXT, encoding="utf-8")).get("records", [])
            for rec in reps:
                for p in (rec.get("Collections_Rep__c") or "").split(";"):
                    if p.strip():
                        rep_names.add(p.strip())
        except Exception:
            pass
        return accts, rep_names, "Salesforce (saved snapshot — sandbox live pending app config)"


# ── name matching (from build_hybrid_snapshot) ─────────────────────────────
SUFFIX_RE = re.compile("|".join([r",\s*llc", r",\s*inc\.", r",\s*inc", r"\sinc\b", r"\sllc\b",
                                 r",\s*ltd", r"\sltd\b", r"\scorp\b", r"\scorporation\b", r",\s*corp"]), re.I)
NS_PREFIX_RE = re.compile(r"^\d+ADV\s+", re.I)
strip_ns = lambda n: NS_PREFIX_RE.sub("", n).strip()


def norm(n):
    n = re.sub(r"\s*\(.*?\)", "", n.lower().strip())
    return re.sub(r"\s+", " ", SUFFIX_RE.sub("", n)).strip()


def build():
    ns_customers, entity_primary_rep, full_aging, cash, approaching = fetch_netsuite()
    sf_accounts, sf_rep_names, sf_source = fetch_salesforce()

    sf_full = {}
    sf_pref = defaultdict(list)
    for a in sf_accounts:
        nm = norm(a.get("Name", ""))
        sf_full[nm] = a
        sf_pref[nm[:25]].append(a)

    def match(ns_name):
        nm = norm(strip_ns(ns_name))
        if nm in sf_full:
            return sf_full[nm]
        c = sf_pref.get(nm[:25], [])
        return c[0] if c else None

    merged, matched = [], 0
    for ns in ns_customers:
        sf = match(ns["entityname"])
        matched += 1 if sf else 0
        merged.append({**ns, "clean_name": strip_ns(ns["entityname"]),
                       "primary_rep": entity_primary_rep.get(ns["entity"]), "sf": sf})

    flag = lambda r, f: bool(r["sf"].get(f)) if r["sf"] else False
    val = lambda r, f: (r["sf"].get(f) if r["sf"] else None)
    overdue_60 = [r for r in merged if r["max_dpd"] >= 60]
    topN = lambda lst, balkey="total_overdue", n=5: [{"id": r["entity"], "name": r["clean_name"], "balance": round(r[balkey]), "dpd": round(r["max_dpd"])}
                             for r in sorted(lst, key=lambda x: x[balkey], reverse=True)[:n]]

    # dpd buckets (60+)
    def bkt(d):
        return ("60–89 DPD" if d <= 89 else "90–119 DPD" if d <= 119 else "120–179 DPD"
                if d <= 179 else "180–364 DPD" if d <= 364 else "365+ DPD")
    bd = defaultdict(lambda: {"accounts": 0, "balance": 0.0})
    for r in overdue_60:
        b = bkt(r["max_dpd"]); bd[b]["accounts"] += 1; bd[b]["balance"] += r["total_overdue"]
    dpdBreakdown = [{"bucket": b, "accounts": bd[b]["accounts"], "balance": round(bd[b]["balance"])}
                    for b in ["60–89 DPD", "90–119 DPD", "120–179 DPD", "180–364 DPD", "365+ DPD"]]

    on_hold = [r for r in merged if r["max_dpd"] >= 1 and flag(r, "Support_Hold__c")]
    missing = [r for r in merged if r["max_dpd"] >= 45 and (r["sf"] is None or not any(
        flag(r, f) for f in ["Support_Hold__c", "Strategic_Account__c", "Strategic_Account_Child__c",
                             "Stop_Hold_Override__c", "Account_Litigation_Hold__c", "Bankruptcy_Hold__c"]))]
    blockers = ["Support_Hold__c", "Account_Litigation_Hold__c", "Bankruptcy_Hold__c", "X3rd_Party_Collections__c"]
    elig = [r for r in overdue_60 if r["sf"] is None or not any(flag(r, f) for f in blockers)]
    blocked = [r for r in overdue_60 if r["sf"] and any(flag(r, f) for f in blockers[:3])]
    woff = [r for r in merged if r["max_dpd"] >= 180]
    legal = [r for r in merged if r["max_dpd"] >= 1 and r["sf"] and (flag(r, "Account_Litigation_Hold__c") or flag(r, "Bankruptcy_Hold__c"))]
    demand = [r for r in overdue_60 if r["sf"] is None or not any(flag(r, f) for f in ["Account_Litigation_Hold__c", "Bankruptcy_Hold__c", "Support_Hold__c", "X3rd_Party_Collections__c"])]
    extreme = [r for r in merged if r["max_dpd"] >= 365]
    stops = [r for r in merged if r["max_dpd"] >= 30 and flag(r, "Stop_Hold_Override__c")]
    strat = [r for r in merged if r["max_dpd"] >= 30 and (flag(r, "Strategic_Account__c") or flag(r, "Strategic_Account_Child__c"))]
    pending = [r for r in merged if r["max_dpd"] >= 1 and flag(r, "Possible_Pending_Hold__c") and not flag(r, "Support_Hold__c")]

    # reps + repAccounts
    rep_agg = defaultdict(lambda: {"accounts": 0, "balance": 0.0})
    rep_accts = defaultdict(list)
    for r in overdue_60:
        rep = r.get("primary_rep") or "Unassigned"
        rep_agg[rep]["accounts"] += 1; rep_agg[rep]["balance"] += r["total_overdue"]
        rep_accts[rep].append({"name": r["clean_name"], "balance": round(r["total_overdue"]), "dpd": round(r["max_dpd"])})
    collectionsReps = sorted([{"rep": k, "accounts": v["accounts"], "balance": round(v["balance"])} for k, v in rep_agg.items()],
                             key=lambda x: x["balance"], reverse=True)[:10]
    repAccounts = {k: sorted(v, key=lambda x: x["balance"], reverse=True) for k, v in rep_accts.items()}

    sf_rep_combined = " | ".join(sf_rep_names).lower()
    inactive = defaultdict(int)
    for r in overdue_60:
        rep = r.get("primary_rep")
        if rep and rep.lower() not in sf_rep_combined:
            inactive[rep] += 1
    inactive_reps = sorted([{"repName": k, "accountCount": v} for k, v in inactive.items()], key=lambda x: x["accountCount"], reverse=True)
    inactiveRepAccounts = {k: repAccounts.get(k, []) for k in inactive}

    sf_hold_accts = [a for a in sf_accounts if a.get("Support_Hold__c")]
    matched_hold_ids = {r["sf"]["Id"] for r in merged if r["sf"] and r["max_dpd"] >= 1}
    sf_holds = [{"name": a.get("Name", ""), "accountManager": a.get("Owner_Name", ""), "rep": a.get("Collections_Rep__c", "")} for a in sf_hold_accts]
    matched_h = sum(1 for a in sf_hold_accts if a.get("Id") in matched_hold_ids)

    taa_mgr = [r for r in overdue_60 if r["sf"] and val(r, "Owner_Name") not in (None, "", "Open - RevOps")]

    snap = {
        "_mode": "hybrid-live", "_generatedAt": datetime.now(timezone.utc).isoformat(),
        "_sources": {"ns": "NetSuite production (live SuiteQL)", "sf": sf_source},
        "_stats": {"nsCustomers": len(ns_customers), "sfAccounts": len(sf_accounts), "matchedAccounts": matched},
        "overdueBalance": {"total": round(sum(r["total_overdue"] for r in overdue_60)), "accountCount": len(overdue_60)},
        "atRisk": {"total": round(sum(r["total_overdue"] for r in overdue_60)), "accountCount": len(overdue_60), "topAccounts": topN(overdue_60)},
        "dpdBreakdown": dpdBreakdown,
        # flag tiles span <60 DPD too, so they use each account's full overdue (bal_all)
        "supportHolds": {"onHoldCount": len(on_hold), "onHoldBalance": round(sum(r["bal_all"] for r in on_hold)),
                         "missingHoldCount": len(missing), "missingHoldBalance": round(sum(r["bal_all"] for r in missing))},
        "placementQueue": {"eligibleCount": len(elig), "eligibleBalance": round(sum(r["total_overdue"] for r in elig)),
                           "blockedCount": len(blocked), "topAccounts": topN(elig)},
        "writeOffPool": {"candidateCount": len(woff), "candidateBalance": round(sum(r["bal_180"] for r in woff)), "topAccounts": topN(woff, "bal_180")},
        "legalBlocked": {"count": len(legal), "balance": round(sum(r["bal_all"] for r in legal))},
        "demandLetterQueue": {"count": len(demand), "balance": round(sum(r["total_overdue"] for r in demand))},
        "extremeDPD": {"count": len(extreme), "balance": round(sum(r["bal_365"] for r in extreme))},
        "stopHoldOverrides": {"count": len(stops), "balance": round(sum(r["bal_all"] for r in stops))},
        "strategicWatch": {"count": len(strat), "balance": round(sum(r["bal_all"] for r in strat))},
        "possiblePendingHolds": {"count": len(pending), "balance": round(sum(r["bal_all"] for r in pending))},
        "collectionsReps": collectionsReps,
        "holdsComparison": {"sfHoldCount": len(sf_hold_accts), "sfHolds": sf_holds, "nsMatchedHoldCount": matched_h,
                            "nsUnmatchedHoldCount": len(sf_hold_accts) - matched_h},
        "taaChecks": {"eligibleCount": len(overdue_60), "withManagerCount": len(taa_mgr),
                      "withoutManagerCount": len(overdue_60) - len(taa_mgr), "inactiveReps": inactive_reps},
        "repAccounts": repAccounts, "inactiveRepAccounts": inactiveRepAccounts,
        "fullAging": full_aging, "cashCollected": cash, "approaching": approaching,
        "sfBaseUrl": "https://advantive.lightning.force.com",
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH):,} bytes)")
    print(f"  overdue 60+: ${snap['overdueBalance']['total']:,} / {snap['overdueBalance']['accountCount']} accts")
    print(f"  full AR total: ${round(sum(full_aging.values())):,} | cash MTD ${cash['mtd']:,.0f} QTD ${cash['qtd']:,.0f}")
    print(f"  SF source: {sf_source}")
    return snap


if __name__ == "__main__":
    build()
