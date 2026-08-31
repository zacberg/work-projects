#!/usr/bin/env python3
"""
Build hybrid AR collections dashboard snapshot by merging NetSuite and Salesforce data.
"""

import json
import re
import os
from collections import defaultdict
from datetime import datetime, timezone

# ─── File paths ────────────────────────────────────────────────────────────────
BASE = r"C:\Users\ZachBergman\.claude\projects\C--Users-ZachBergman\0fa1c09c-26c0-421b-8cf9-3e9acb6f3a42\tool-results"

NS_CUSTOMERS_JSONL  = os.path.join(BASE, "ns_customers_parsed.jsonl")
SF_FLAGS_JSON       = os.path.join(BASE, "sf_account_flags_compact.json")
NS_REPS_TXT         = os.path.join(BASE, "mcp-claude_ai_NetSuite-ns_runCustomSuiteQL-1780491430369.txt")
SF_REPS_TXT         = os.path.join(BASE, "mcp-claude_ai_Advantive_Salesforce-soqlQueryplatform_sobject_reads-1780491428498.txt")

OUTPUT_PATH = r"C:\Users\ZachBergman\ar-dashboard\hybrid-snapshot.json"

# ─── Load NS customers ──────────────────────────────────────────────────────────
print("Loading NS customers...")
ns_customers = []
with open(NS_CUSTOMERS_JSONL, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            # handle both JSONL (one per line) and single JSON array
            try:
                obj = json.loads(line)
                if isinstance(obj, list):
                    ns_customers.extend(obj)
                else:
                    ns_customers.append(obj)
            except json.JSONDecodeError:
                pass

print(f"  NS customers loaded: {len(ns_customers)}")

# ─── Load SF account flags ──────────────────────────────────────────────────────
print("Loading SF account flags...")
with open(SF_FLAGS_JSON, encoding="utf-8") as f:
    raw = f.read().strip()

# It may be a JSON array or JSONL
if raw.startswith("["):
    sf_accounts = json.loads(raw)
else:
    sf_accounts = []
    for line in raw.splitlines():
        line = line.strip()
        if line:
            try:
                sf_accounts.append(json.loads(line))
            except:
                pass

print(f"  SF accounts loaded: {len(sf_accounts)}")

# ─── Load NS rep assignments ────────────────────────────────────────────────────
print("Loading NS rep assignments...")
with open(NS_REPS_TXT, encoding="utf-8") as f:
    ns_reps_raw = f.read()

ns_reps_data = json.loads(ns_reps_raw)
ns_reps_rows = ns_reps_data.get("data", [])
print(f"  NS rep rows loaded: {len(ns_reps_rows)}")

# Build primary rep per entity (most frequent rep_name for that entity)
entity_rep_counts = defaultdict(lambda: defaultdict(int))
for row in ns_reps_rows:
    entity = row.get("entity")
    rep = row.get("rep_name", "").strip()
    if entity and rep:
        entity_rep_counts[entity][rep] += 1

entity_primary_rep = {}
for entity, rep_counts in entity_rep_counts.items():
    entity_primary_rep[entity] = max(rep_counts, key=rep_counts.get)

print(f"  Entities with rep assignments: {len(entity_primary_rep)}")

# ─── Load SF active rep names ────────────────────────────────────────────────────
print("Loading SF active rep names...")
with open(SF_REPS_TXT, encoding="utf-8") as f:
    sf_reps_raw = f.read()

sf_reps_data = json.loads(sf_reps_raw)
sf_reps_records = sf_reps_data.get("records", [])

sf_active_rep_names = set()
for rec in sf_reps_records:
    rep_field = rec.get("Collections_Rep__c", "")
    if rep_field:
        for part in rep_field.split(";"):
            name = part.strip()
            if name:
                sf_active_rep_names.add(name)

print(f"  SF active rep names: {len(sf_active_rep_names)}")

# ─── Name normalization ─────────────────────────────────────────────────────────

LEGAL_SUFFIXES = [
    r",\s*llc", r",\s*inc\.", r",\s*inc", r"\sinc\b", r"\sllc\b",
    r",\s*ltd", r"\sltd\b", r"\scorp\b", r"\scorporation\b", r",\s*corp"
]
SUFFIX_RE = re.compile("|".join(LEGAL_SUFFIXES), re.IGNORECASE)

NS_PREFIX_RE = re.compile(r"^\d+ADV\s+", re.IGNORECASE)

def strip_ns_prefix(name: str) -> str:
    """Remove leading digits + 'ADV ' prefix from NS name."""
    return NS_PREFIX_RE.sub("", name).strip()

def normalize_name(name: str) -> str:
    """Normalize a company name for matching."""
    name = name.lower().strip()
    # Remove content in parentheses (city info)
    name = re.sub(r"\s*\(.*?\)", "", name)
    name = SUFFIX_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def extract_city(name: str) -> str:
    """Extract city name from parentheses."""
    m = re.search(r"\(([^,)]+)", name)
    if m:
        return m.group(1).strip().lower()
    return ""

def first_word(name: str) -> str:
    """Get first word of a normalized name."""
    parts = normalize_name(name).split()
    return parts[0] if parts else ""

# Build SF lookup structures
# Key: first 25 chars of normalized name → list of SF account dicts
sf_norm_map = defaultdict(list)
sf_full_norm_map = {}  # full normalized name → SF account

for acct in sf_accounts:
    raw_name = acct.get("Name", "")
    norm = normalize_name(raw_name)
    key25 = norm[:25]
    sf_norm_map[key25].append(acct)
    sf_full_norm_map[norm] = acct

# Also build: (first_word, city) → SF account for fallback
sf_word_city_map = defaultdict(list)
for acct in sf_accounts:
    raw_name = acct.get("Name", "")
    fw = first_word(raw_name)
    city = extract_city(raw_name)
    if fw:
        sf_word_city_map[(fw, city)].append(acct)

def find_sf_match(ns_name: str):
    """
    Try to find a matching SF account for an NS customer name.
    Returns (sf_account_or_None, match_quality)
    """
    clean = strip_ns_prefix(ns_name)
    norm = normalize_name(clean)
    key25 = norm[:25]

    # Exact normalized match
    if norm in sf_full_norm_map:
        return sf_full_norm_map[norm], "exact"

    # 25-char prefix match
    candidates = sf_norm_map.get(key25, [])
    if len(candidates) == 1:
        return candidates[0], "partial"
    if len(candidates) > 1:
        # pick best candidate - longest common prefix
        best = max(candidates, key=lambda a: len(os.path.commonprefix([norm, normalize_name(a.get("Name",""))])))
        return best, "partial"

    # Fallback: first word + city
    fw = first_word(clean)
    city = extract_city(clean)
    fb_candidates = sf_word_city_map.get((fw, city), [])
    if fb_candidates:
        return fb_candidates[0], "partial"

    return None, "none"

# ─── Build merged dataset ───────────────────────────────────────────────────────
print("Matching NS customers to SF accounts...")

matched_count = 0
merged = []

for ns in ns_customers:
    entity = ns["entity"]
    ns_name = ns["entityname"]
    max_dpd = float(ns["max_dpd"])
    total_overdue = float(ns["total_overdue"])
    invoice_count = int(ns["invoice_count"])
    clean_name = strip_ns_prefix(ns_name)
    primary_rep = entity_primary_rep.get(entity)

    sf_acct, match_quality = find_sf_match(ns_name)

    if sf_acct:
        matched_count += 1

    merged.append({
        "entity": entity,
        "ns_name": ns_name,
        "clean_name": clean_name,
        "max_dpd": max_dpd,
        "total_overdue": total_overdue,
        "invoice_count": invoice_count,
        "primary_rep": primary_rep,
        "sf": sf_acct,
        "match_quality": match_quality,
    })

print(f"  Matched {matched_count} of {len(ns_customers)} NS customers to SF accounts")

# Helper accessors
def sf_flag(row, field, default=False):
    if row["sf"] is None:
        return default
    return bool(row["sf"].get(field, default))

def sf_val(row, field, default=None):
    if row["sf"] is None:
        return default
    return row["sf"].get(field, default)

# ─── Metrics ────────────────────────────────────────────────────────────────────

# overdueBalance (60+ DPD)
overdue_60 = [r for r in merged if r["max_dpd"] >= 60]
overdueBalance = {
    "total": round(sum(r["total_overdue"] for r in overdue_60)),
    "accountCount": len(overdue_60),
}
print(f"overdueBalance: {overdueBalance}")

# atRisk (60+ DPD) — same as overdueBalance per instructions
at_risk_sorted = sorted(overdue_60, key=lambda r: r["total_overdue"], reverse=True)
atRisk = {
    "total": overdueBalance["total"],
    "accountCount": overdueBalance["accountCount"],
    "topAccounts": [
        {
            "id": r["entity"],
            "name": r["clean_name"],
            "balance": round(r["total_overdue"]),
            "dpd": round(r["max_dpd"]),
        }
        for r in at_risk_sorted[:5]
    ],
}
print(f"atRisk: total={atRisk['total']}, count={atRisk['accountCount']}")

# dpdBreakdown
def dpd_bucket(row):
    d = row["max_dpd"]
    if 60 <= d <= 89: return "60–89 DPD"
    if 90 <= d <= 119: return "90–119 DPD"
    if 120 <= d <= 179: return "120–179 DPD"
    if 180 <= d <= 364: return "180–364 DPD"
    if d >= 365: return "365+ DPD"
    return None

bucket_data = defaultdict(lambda: {"accounts": 0, "balance": 0.0})
bucket_order = ["60–89 DPD", "90–119 DPD", "120–179 DPD", "180–364 DPD", "365+ DPD"]
for r in merged:
    b = dpd_bucket(r)
    if b:
        bucket_data[b]["accounts"] += 1
        bucket_data[b]["balance"] += r["total_overdue"]

dpdBreakdown = [
    {
        "bucket": b,
        "accounts": bucket_data[b]["accounts"],
        "balance": round(bucket_data[b]["balance"]),
    }
    for b in bucket_order
]
print(f"dpdBreakdown: {[(d['bucket'], d['accounts']) for d in dpdBreakdown]}")

# supportHolds
on_hold = [
    r for r in merged
    if r["max_dpd"] >= 1 and sf_flag(r, "Support_Hold__c")
]
# missingHold: 45+ DPD, no SF match OR (SF match but not on support_hold AND not strategic AND not override AND not legal)
missing_hold = [
    r for r in merged
    if r["max_dpd"] >= 45
    and (
        r["sf"] is None
        or (
            not sf_flag(r, "Support_Hold__c")
            and not sf_flag(r, "Strategic_Account__c")
            and not sf_flag(r, "Strategic_Account_Child__c")
            and not sf_flag(r, "Stop_Hold_Override__c")
            and not sf_flag(r, "Account_Litigation_Hold__c")
            and not sf_flag(r, "Bankruptcy_Hold__c")
        )
    )
]
supportHolds = {
    "onHoldCount": len(on_hold),
    "onHoldBalance": round(sum(r["total_overdue"] for r in on_hold)),
    "missingHoldCount": len(missing_hold),
    "missingHoldBalance": round(sum(r["total_overdue"] for r in missing_hold)),
}
print(f"supportHolds: {supportHolds}")

# placementQueue (TAA eligible — 60+ DPD, not on blocking hold)
placement_eligible = [
    r for r in overdue_60
    if r["sf"] is None or (
        not sf_flag(r, "Support_Hold__c")
        and not sf_flag(r, "Account_Litigation_Hold__c")
        and not sf_flag(r, "Bankruptcy_Hold__c")
        and not sf_flag(r, "X3rd_Party_Collections__c")
    )
]
placement_blocked = [
    r for r in overdue_60
    if r["sf"] is not None and (
        sf_flag(r, "Support_Hold__c")
        or sf_flag(r, "Account_Litigation_Hold__c")
        or sf_flag(r, "Bankruptcy_Hold__c")
    )
]
placement_eligible_sorted = sorted(placement_eligible, key=lambda r: r["total_overdue"], reverse=True)
placementQueue = {
    "eligibleCount": len(placement_eligible),
    "eligibleBalance": round(sum(r["total_overdue"] for r in placement_eligible)),
    "blockedCount": len(placement_blocked),
    "topAccounts": [
        {
            "id": r["entity"],
            "name": r["clean_name"],
            "balance": round(r["total_overdue"]),
            "dpd": round(r["max_dpd"]),
        }
        for r in placement_eligible_sorted[:5]
    ],
}
print(f"placementQueue: eligible={placementQueue['eligibleCount']}, blocked={placementQueue['blockedCount']}")

# writeOffPool (180+ DPD)
writeoff_candidates = [r for r in merged if r["max_dpd"] >= 180]
writeoff_sorted = sorted(writeoff_candidates, key=lambda r: r["total_overdue"], reverse=True)
writeOffPool = {
    "candidateCount": len(writeoff_candidates),
    "candidateBalance": round(sum(r["total_overdue"] for r in writeoff_candidates)),
    "topAccounts": [
        {
            "id": r["entity"],
            "name": r["clean_name"],
            "balance": round(r["total_overdue"]),
            "dpd": round(r["max_dpd"]),
        }
        for r in writeoff_sorted[:5]
    ],
}
print(f"writeOffPool: count={writeOffPool['candidateCount']}, balance={writeOffPool['candidateBalance']}")

# legalBlocked (SF litigation or bankruptcy hold, NS overdue >= 1 DPD)
legal_blocked = [
    r for r in merged
    if r["max_dpd"] >= 1
    and r["sf"] is not None
    and (sf_flag(r, "Account_Litigation_Hold__c") or sf_flag(r, "Bankruptcy_Hold__c"))
]
legalBlocked = {
    "count": len(legal_blocked),
    "balance": round(sum(r["total_overdue"] for r in legal_blocked)),
}
print(f"legalBlocked: {legalBlocked}")

# demandLetterQueue (60+ DPD, not legally blocked, not on hold, not TAA placed)
demand_letter = [
    r for r in overdue_60
    if r["sf"] is None or (
        not sf_flag(r, "Account_Litigation_Hold__c")
        and not sf_flag(r, "Bankruptcy_Hold__c")
        and not sf_flag(r, "Support_Hold__c")
        and not sf_flag(r, "X3rd_Party_Collections__c")
    )
]
demandLetterQueue = {
    "count": len(demand_letter),
    "balance": round(sum(r["total_overdue"] for r in demand_letter)),
}
print(f"demandLetterQueue: {demandLetterQueue}")

# extremeDPD (365+ DPD)
extreme_dpd = [r for r in merged if r["max_dpd"] >= 365]
extremeDPD = {
    "count": len(extreme_dpd),
    "balance": round(sum(r["total_overdue"] for r in extreme_dpd)),
}
print(f"extremeDPD: {extremeDPD}")

# stopHoldOverrides (SF stop_hold_override=true, NS 30+ DPD)
stop_overrides = [
    r for r in merged
    if r["max_dpd"] >= 30 and sf_flag(r, "Stop_Hold_Override__c")
]
stopHoldOverrides = {
    "count": len(stop_overrides),
    "balance": round(sum(r["total_overdue"] for r in stop_overrides)),
}
print(f"stopHoldOverrides: {stopHoldOverrides}")

# strategicWatch (SF strategic account, NS 30+ DPD)
strategic_watch = [
    r for r in merged
    if r["max_dpd"] >= 30
    and (sf_flag(r, "Strategic_Account__c") or sf_flag(r, "Strategic_Account_Child__c"))
]
strategicWatch = {
    "count": len(strategic_watch),
    "balance": round(sum(r["total_overdue"] for r in strategic_watch)),
}
print(f"strategicWatch: {strategicWatch}")

# possiblePendingHolds (SF possible_pending=true, not on support hold, NS 1+ DPD)
possible_pending = [
    r for r in merged
    if r["max_dpd"] >= 1
    and sf_flag(r, "Possible_Pending_Hold__c")
    and not sf_flag(r, "Support_Hold__c")
]
possiblePendingHolds = {
    "count": len(possible_pending),
    "balance": round(sum(r["total_overdue"] for r in possible_pending)),
}
print(f"possiblePendingHolds: {possiblePendingHolds}")

# collectionsReps (60+ DPD, by rep)
rep_data = defaultdict(lambda: {"accounts": 0, "balance": 0.0})
for r in overdue_60:
    rep = r.get("primary_rep") or "Unassigned"
    rep_data[rep]["accounts"] += 1
    rep_data[rep]["balance"] += r["total_overdue"]

collectionsReps = sorted(
    [
        {"rep": rep, "accounts": data["accounts"], "balance": round(data["balance"])}
        for rep, data in rep_data.items()
    ],
    key=lambda x: x["balance"],
    reverse=True,
)[:10]
print(f"collectionsReps: {len(collectionsReps)} reps")

# holdsComparison
sf_holds_accounts = [a for a in sf_accounts if a.get("Support_Hold__c")]
ns_matched_hold_count = 0
ns_unmatched_hold_count = 0

# Build a quick lookup of SF account IDs that have NS matches with max_dpd >= 1
sf_id_to_ns_matched = {}
for r in merged:
    if r["sf"] is not None and r["max_dpd"] >= 1:
        sf_id_to_ns_matched[r["sf"]["Id"]] = True

sf_holds_list = []
for acct in sf_holds_accounts:
    acct_id = acct.get("Id")
    has_ns = sf_id_to_ns_matched.get(acct_id, False)
    if has_ns:
        ns_matched_hold_count += 1
    else:
        ns_unmatched_hold_count += 1
    sf_holds_list.append({
        "name": acct.get("Name", ""),
        "accountManager": acct.get("Owner_Name", ""),
        "rep": acct.get("Collections_Rep__c", ""),
    })

holdsComparison = {
    "sfHoldCount": len(sf_holds_accounts),
    "sfHolds": sf_holds_list,
    "nsMatchedHoldCount": ns_matched_hold_count,
    "nsUnmatchedHoldCount": ns_unmatched_hold_count,
}
print(f"holdsComparison: sfHoldCount={holdsComparison['sfHoldCount']}, matched={ns_matched_hold_count}, unmatched={ns_unmatched_hold_count}")

# taaChecks
taa_eligible = overdue_60  # NS 60+ DPD
taa_with_manager = [
    r for r in taa_eligible
    if r["sf"] is not None
    and sf_val(r, "Owner_Name")
    and sf_val(r, "Owner_Name") not in ("", "Open - RevOps")
]
taa_without_manager = [
    r for r in taa_eligible
    if r["sf"] is None
    or not sf_val(r, "Owner_Name")
    or sf_val(r, "Owner_Name") in ("", "Open - RevOps")
]

# Inactive reps: NS rep names that do NOT appear as substring of any SF Collections_Rep__c value
all_ns_rep_names = set(entity_primary_rep.values())
# Build the full set of SF Collections_Rep__c strings (not split)
sf_all_rep_strings = set()
for rec in sf_reps_records:
    rep_field = rec.get("Collections_Rep__c", "")
    if rep_field:
        sf_all_rep_strings.add(rep_field)

# Also collect from sf_accounts
for acct in sf_accounts:
    rep_field = acct.get("Collections_Rep__c", "")
    if rep_field:
        sf_all_rep_strings.add(rep_field)

# Combine all SF rep text into one big string for substring search
sf_rep_combined = " | ".join(sf_all_rep_strings).lower()

inactive_reps_data = defaultdict(int)
for r in overdue_60:
    rep = r.get("primary_rep")
    if rep and rep.lower() not in sf_rep_combined:
        inactive_reps_data[rep] += 1

inactive_reps = sorted(
    [{"repName": rep, "accountCount": cnt} for rep, cnt in inactive_reps_data.items()],
    key=lambda x: x["accountCount"],
    reverse=True,
)

taaChecks = {
    "eligibleCount": len(taa_eligible),
    "withManagerCount": len(taa_with_manager),
    "withoutManagerCount": len(taa_without_manager),
    "inactiveReps": inactive_reps,
}
print(f"taaChecks: eligible={taaChecks['eligibleCount']}, withManager={taaChecks['withManagerCount']}, inactiveReps={len(inactive_reps)}")

# ─── Assemble final snapshot ────────────────────────────────────────────────────
snapshot = {
    "_mode": "hybrid-snapshot",
    "_generatedAt": datetime.now(timezone.utc).isoformat(),
    "_sources": {
        "ns": "NetSuite production (live)",
        "sf": "Salesforce production (MCP)",
    },
    "_stats": {
        "nsCustomers": len(ns_customers),
        "sfAccounts": len(sf_accounts),
        "matchedAccounts": matched_count,
    },
    "overdueBalance": overdueBalance,
    "atRisk": atRisk,
    "dpdBreakdown": dpdBreakdown,
    "supportHolds": supportHolds,
    "placementQueue": placementQueue,
    "writeOffPool": writeOffPool,
    "legalBlocked": legalBlocked,
    "demandLetterQueue": demandLetterQueue,
    "extremeDPD": extremeDPD,
    "stopHoldOverrides": stopHoldOverrides,
    "strategicWatch": strategicWatch,
    "possiblePendingHolds": possiblePendingHolds,
    "collectionsReps": collectionsReps,
    "holdsComparison": holdsComparison,
    "taaChecks": taaChecks,
    "sfBaseUrl": "https://advantive.lightning.force.com",
}

# ─── Write output ───────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, indent=2, ensure_ascii=False)

print(f"\nWrote {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")

# Print summary of key metrics
print("\n=== KEY METRICS SUMMARY ===")
print(f"NS Customers: {len(ns_customers)}")
print(f"SF Accounts: {len(sf_accounts)}")
print(f"Matched: {matched_count}")
print(f"")
print(f"overdueBalance (60+ DPD): ${overdueBalance['total']:,} across {overdueBalance['accountCount']} accounts")
print(f"atRisk (60+ DPD): ${atRisk['total']:,} across {atRisk['accountCount']} accounts")
print(f"  Top 5:")
for a in atRisk['topAccounts']:
    print(f"    {a['name'][:50]}: ${a['balance']:,} ({a['dpd']} DPD)")
print(f"")
print(f"dpdBreakdown:")
for d in dpdBreakdown:
    print(f"  {d['bucket']}: {d['accounts']} accounts, ${d['balance']:,}")
print(f"")
print(f"supportHolds: {supportHolds['onHoldCount']} on hold (${supportHolds['onHoldBalance']:,}), {supportHolds['missingHoldCount']} missing (${supportHolds['missingHoldBalance']:,})")
print(f"placementQueue: {placementQueue['eligibleCount']} eligible (${placementQueue['eligibleBalance']:,}), {placementQueue['blockedCount']} blocked")
print(f"writeOffPool: {writeOffPool['candidateCount']} candidates (${writeOffPool['candidateBalance']:,})")
print(f"legalBlocked: {legalBlocked['count']} accounts (${legalBlocked['balance']:,})")
print(f"demandLetterQueue: {demandLetterQueue['count']} accounts (${demandLetterQueue['balance']:,})")
print(f"extremeDPD: {extremeDPD['count']} accounts (${extremeDPD['balance']:,})")
print(f"stopHoldOverrides: {stopHoldOverrides['count']} accounts (${stopHoldOverrides['balance']:,})")
print(f"strategicWatch: {strategicWatch['count']} accounts (${strategicWatch['balance']:,})")
print(f"possiblePendingHolds: {possiblePendingHolds['count']} accounts (${possiblePendingHolds['balance']:,})")
print(f"holdsComparison: {holdsComparison['sfHoldCount']} SF holds, {ns_matched_hold_count} with NS match, {ns_unmatched_hold_count} without")
print(f"taaChecks: {taaChecks['eligibleCount']} eligible, {taaChecks['withManagerCount']} with manager, {len(inactive_reps)} inactive reps")
print(f"  Inactive reps: {[r['repName'] for r in inactive_reps]}")
print(f"")
print(f"collectionsReps (top 10 by balance):")
for r in collectionsReps:
    print(f"  {r['rep']}: {r['accounts']} accounts, ${r['balance']:,}")
