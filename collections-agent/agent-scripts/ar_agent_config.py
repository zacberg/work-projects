"""
AR Collections Agent — Confirmed Configuration
All thresholds, recipients, and business rules confirmed by Jordan Duke.
Upload this file to the ChatGPT agent knowledge base as authoritative reference.
"""

# ─── FEATURE 1: THIRD-PARTY PLACEMENT ────────────────────────────────────────

PLACEMENT_MIN_DPD = 60                  # minimum days past due to be eligible
PLACEMENT_MIN_BALANCE = None            # no dollar floor — unresponsiveness-driven
PLACEMENT_CSM_SILENCE_DAYS = 7         # days without CSM response triggers review
PLACEMENT_AGENCY = "Altus"             # third-party agency name
PLACEMENT_ATTEMPTS_SOURCE = "YayPay"   # NOT CONNECTED — attempts check is manual gap

# Legal_Notes__c behavior for Feature 1:
# - Account_Litigation_Hold__c = true  → BLOCKED (auto-disqualify)
# - Bankruptcy_Hold__c = true          → BLOCKED (auto-disqualify)
# - Legal_Notes__c contains keywords   → REVIEW FLAG (surface for human, do not auto-block)

# ─── FEATURE 2: SUPPORT HOLD AUDIT ───────────────────────────────────────────

HOLD_AUDIT_MIN_DPD = 45                # confirmed Jordan Duke + SF case 01629175 (2026-05-18)
HOLD_AUDIT_MIN_ARR_PCT = 0.15          # 15% of SCG_Active_ARR__c unpaid threshold
# NOTE: Non-Automated SOP says 30 DPD — that applies to manual review process, NOT automated

HOLD_FIELD = "Support_Hold__c"         # ONLY field used for hold state — boolean
# Finance_Hold_Status__c is NOT used — excluded from all queries

# Two-way audit:
# Report 1 — Support_Hold__c = true, Total_Overdue_Balance__c = 0 → recommend release
# Report 2 — Support_Hold__c = false, qualifies by DPD + ARR% → recommend apply hold

# Legal/risk surface fields (do NOT auto-block on these — surface for review only):
HOLD_LEGAL_SURFACE_FIELDS = [
    "Account_Litigation_Hold__c",
    "Bankruptcy_Hold__c",
    "Legal_Notes__c",          # keyword scan: litigation, attorney, bankruptcy, legal hold, settlement
]
# Maintenance_Detail__c is excluded — not confirmed in scope

# Hold threshold email recipients (per account CSM/AM/PS/AR rep — NOT all customers)
# Strategic accounts excluded from automated hold application

# ─── FEATURE 3: CASH UPDATE EMAIL ────────────────────────────────────────────

CASH_UPDATE_SUBJECT = "DELIVERY | Collections Forecast as of {DATE}"

CASH_UPDATE_TO = [
    "kevin.boyce@advantive.com",
    "ryan.ashe@advantive.com",
    "phil.burroughs@advantive.com",
    "jeremy.vanbeusekom@advantive.com",
]

CASH_UPDATE_CC = [
    "joy.jones@advantive.com",
    "jeffery.bartels@advantive.com",
    "justin.wixom@advantive.com",
    "jordan.duke@advantive.com",
]

CASH_UPDATE_RULES = {
    "friday": "suppress Path to Target section entirely",
    "tuesday": "include Checks in Transit line — source: Josh Snow via Teams 'Cash App Updates' chat",
    "overdue_balance_source": "Salesforce — Total_Overdue_Balance__c, Days_Overdue__c >= 60",
    "cash_collected_source": "AR Tracker SharePoint — cell B7",
    "target_source": "AR Tracker SharePoint — cell B8",
    "ptp_source": "MANUAL GAP — YayPay not connected, always placeholder",
}

# AR Tracker section label: always "Collections PEQs" — never "forecast inputs" or any other label

# ─── FEATURE 4: EMAIL DRAFTING / INBOUND MONITORING ──────────────────────────

SHARED_INBOX = "receivables@advantive.com"  # linked to YayPay; rep mailboxes also receive

YAYPAY_COORDINATION = (
    "Agent runs ALONGSIDE YayPay dunning — does NOT replace it. "
    "YayPay sends automated emails by DPD tier and payer quality. "
    "Agent drafts personal/escalation emails to supplement. "
    "Do NOT duplicate or conflict with YayPay sequences."
)

DUNNING_BLOCK_FIELDS = {
    "custentityadv_pause_dunning": "NetSuite — if true, exclude from dunning",
    "custentity_atlas_blockcolemail": "NetSuite — if true, block collections email entirely",
}

# Six confirmed tone modes (Jordan Duke email examples):
TONE_MODES = {
    "Friendly/Collaborative":        "hold lifted, billing ops intro, partnership framing",
    "Firm but Professional":         "missed commitment, re-commitment request",
    "Internal Action Required":      "pre-placement CSM/AM review window",
    "Urgent Vendor Escalation":      "system failure, YayPay mailing module issue",
    "Legal/Ownership/Remediation":   "settlement oversight, legal escalation",
    "Executive/Leadership Update":   "cash meeting summary, leadership-facing blurb",
}

# ─── FEATURE 5: PORTAL / BILLING CASE TRACKER ────────────────────────────────

PORTAL_CASE_KEYWORDS_SUBJECT = [
    "portal", "upload", "tax", "ariba", "coupa",
    "w-9", "w-8", "purchase order", "po number",
]
PORTAL_CASE_TYPE = "Billing"
# Description LIKE conditions are REMOVED — too slow and unreliable

# ─── FEATURE 6: WRITE-OFF REVIEW ─────────────────────────────────────────────

WRITEOFF_BALANCE_FIELD = "Total_Overdue_Balance__c"   # always use this — NOT Open_Balance__c
# When Total_Overdue_Balance__c differs from Open_Balance__c by >$10,000 — show both labeled

WRITEOFF_APPROVERS = [
    "justin.wixom@advantive.com",   # Sr Dir Finance Ops
    "joy.jones@advantive.com",      # Controller
]

# ─── FEATURE 7: LEGAL / LITIGATION HOLD CHECK ────────────────────────────────

# THREE states:
# CLEAR        — no flags, proceed
# BLOCKED      — Account_Litigation_Hold__c = true OR Bankruptcy_Hold__c = true → stop, do not contact
# REVIEW FLAG  — Legal_Notes__c contains keywords → surface for human review, do not auto-block

LEGAL_KEYWORDS = [
    "litigation", "attorney", "bankruptcy", "legal hold", "settlement", "lawsuit", "counsel"
]

# Feature 7 gates Features 1 and 11 — must run first

# ─── FEATURE 8: PAYMENT PLAN RISK REVIEW ─────────────────────────────────────

PAYMENT_PLAN_APPROVER = "jordan.duke@advantive.com"   # no dollar threshold
PAYMENT_PLAN_QUERY_MODE = {
    "specific_account": "WHERE Name LIKE '%[name]%' AND IsDeleted = false LIMIT 5",
    "portfolio_scan":   "WHERE Total_Overdue_Balance__c > 0 ORDER BY Total_Overdue_Balance__c DESC LIMIT 100",
}

# ─── FEATURE 11: DEMAND LETTERS ──────────────────────────────────────────────

# Requires Feature 7 check first — BLOCKED accounts never receive demand letters
# Templates: demand letter, termination notice — to be added to knowledge files

# ─── CONFIRMED CONTACTS ──────────────────────────────────────────────────────

CONTACTS = {
    "jordan_duke":         "jordan.duke@advantive.com",      # AR Sr Manager — feature owner; phone (656) 444-9887 confirmed via SF case 01629175 email signature
    "justin_wixom":        "justin.wixom@advantive.com",     # Sr Dir Finance Ops
    "joy_jones":           "joy.jones@advantive.com",        # Controller
    "ryan_ashe":           "ryan.ashe@advantive.com",        # CFO
    "jeffery_bartels":     "jeffery.bartels@advantive.com",
    "kevin_boyce":         "kevin.boyce@advantive.com",
    "phil_burroughs":      "phil.burroughs@advantive.com",
    "jeremy_vanbeusekom":  "jeremy.vanbeusekom@advantive.com",
    "josh_snow":           "joshua.snow@advantive.com",      # checks in transit, Tuesdays
    "tiffany_johnson":     "tiffany.johnson@advantive.com",  # Billing Ops Manager
    "gaby_vitoria":        "gaby.vitoria@advantive.com",     # settlement, weekly meetings with Jordan
}

# ─── BASELINE METRICS ────────────────────────────────────────────────────────

DSO = 38                        # as of 2026-05-27
CEI = None                      # not yet tracked; Jordan establishing baseline over next month

# ─── SYSTEM RULES ────────────────────────────────────────────────────────────

SHADOW_MODE = True              # agent drafts only — never executes writes, sends, or closes
YAYPAY_CONNECTED = False        # outreach attempts (F1) and PTP (F3) are manual gaps
NETSUITE_CROSSWALK = None       # Harmony_Customer_ID__c ↔ NetSuite entity ID mapping unconfirmed
