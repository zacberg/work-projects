"""
AR Collections Agent — All SOQL Queries
Confirmed field names and query patterns for all 11 features.
Upload this file to the ChatGPT agent knowledge base as authoritative reference.
These are the exact queries the agent should use — do not modify field names.
"""

# ─── FEATURE 1: THIRD-PARTY PLACEMENT CANDIDATES ─────────────────────────────

PLACEMENT_CANDIDATES_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c, Open_Balance__c,
       SCG_Active_ARR__c, Support_Hold__c, Stop_Hold_Override__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c, Legal_Notes__c,
       X3rd_Party_Collections__c, Strategic_Account__c,
       Strategic_Account_Child__c, CSM_Name_Text__c, Billing_Email_s__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 5)
FROM Account
WHERE Days_Overdue__c >= 60
  AND X3rd_Party_Collections__c = false
  AND IsDeleted = false
ORDER BY Days_Overdue__c DESC
LIMIT 200
"""
# After retrieving: run Feature 7 legal check on each candidate
# Group by CSM_Name_Text__c for the CSM review email
# Flag null CSM or 'CSM Pool' accounts separately

# ─── FEATURE 2: SUPPORT HOLD AUDIT ───────────────────────────────────────────

HOLD_AUDIT_QUERY = """
SELECT Id, Name, Support_Hold__c, Total_Overdue_Balance__c,
       Open_Balance__c, Days_Overdue__c, SCG_Active_ARR__c,
       Strategic_Account__c, Stop_Hold_Override__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       Finance_Hold_Exemption_Status__c, Legal_Notes__c,
       Possible_Pending_Hold__c,
       (SELECT Id, Support_Hold__c FROM Revenue_Entities__r
        WHERE Support_Hold__c = true LIMIT 10)
FROM Account
WHERE (Support_Hold__c = true
    OR Possible_Pending_Hold__c = true
    OR Days_Overdue__c >= 45
    OR Bankruptcy_Hold__c = true
    OR Account_Litigation_Hold__c = true)
  AND IsDeleted = false
ORDER BY Days_Overdue__c DESC NULLS LAST
LIMIT 500
"""
# Report 1: Support_Hold__c = true AND Total_Overdue_Balance__c = 0 → recommend release
# Report 2: Support_Hold__c = false AND qualifies by DPD/ARR% → recommend apply hold
# Qualify for Report 2: Days_Overdue__c >= 45 AND (Total_Overdue_Balance__c / SCG_Active_ARR__c) >= 0.15
# Finance_Hold_Status__c is NOT used — excluded intentionally

# ─── FEATURE 3: CASH UPDATE — OVERDUE BALANCE (>60 DAY) ──────────────────────

CASH_UPDATE_OVERDUE_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       CSM_Name_Text__c, Strategic_Account__c
FROM Account
WHERE Days_Overdue__c >= 60
  AND Total_Overdue_Balance__c > 0
  AND IsDeleted = false
ORDER BY Total_Overdue_Balance__c DESC
LIMIT 200
"""
# Cash collected (B7) and target (B8) come from AR Tracker SharePoint — not Salesforce
# PTP is manual gap — YayPay not connected

# ─── FEATURE 4: EMAIL DRAFTING — ACCOUNT LOOKUP ──────────────────────────────

EMAIL_DRAFT_ACCOUNT_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Stop_Hold_Override__c, Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       Legal_Notes__c, CSM_Name_Text__c, Billing_Email_s__c,
       Possible_Pending_Hold__c, X3rd_Party_Collections__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 5),
       (SELECT Id, Subject, Status, Type, CreatedDate
        FROM Cases WHERE IsClosed = false ORDER BY CreatedDate DESC LIMIT 5)
FROM Account
WHERE Name LIKE '%{account_name}%'
  AND IsDeleted = false
LIMIT 5
"""
# Before drafting: run pre-draft checks —
# 1. Feature 7 legal check
# 2. Stop_Hold_Override__c flag
# 3. Open opportunities within 30 days
# 4. NetSuite caution fields (pause_dunning, blockcolemail)
# 5. Outlook prior outreach check

# ─── FEATURE 5: PORTAL / BILLING CASE TRACKER ────────────────────────────────

PORTAL_CASE_QUERY = """
SELECT Id, Subject, Status, Type, Priority, CreatedDate,
       Account.Name, Account.Total_Overdue_Balance__c,
       Account.Days_Overdue__c, Account.Open_Balance__c
FROM Case
WHERE IsClosed = false
  AND (Subject LIKE '%portal%'
    OR Subject LIKE '%upload%'
    OR Subject LIKE '%tax%'
    OR Subject LIKE '%ariba%'
    OR Subject LIKE '%coupa%'
    OR Subject LIKE '%w-9%'
    OR Subject LIKE '%w-8%'
    OR Subject LIKE '%purchase order%'
    OR Subject LIKE '%po number%'
    OR Type = 'Billing')
ORDER BY CreatedDate DESC
LIMIT 200
"""
# Description LIKE conditions removed — too slow and unreliable

# ─── FEATURE 6: WRITE-OFF REVIEW ─────────────────────────────────────────────

WRITEOFF_CANDIDATES_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Stop_Hold_Override__c, Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       Account_Litigation_Hold__c, Legal_Notes__c,
       X3rd_Party_Collections__c, Strategic_Account__c,
       CSM_Name_Text__c, Billing_Email_s__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false LIMIT 3),
       (SELECT Id, Subject, Status, Type, CreatedDate
        FROM Cases WHERE IsClosed = false LIMIT 5)
FROM Account
WHERE Total_Overdue_Balance__c > 0
  AND Days_Overdue__c >= 90
  AND IsDeleted = false
ORDER BY Total_Overdue_Balance__c DESC
LIMIT 100
"""
# ALWAYS use Total_Overdue_Balance__c for overdue amounts — never Open_Balance__c alone
# If Total_Overdue_Balance__c differs from Open_Balance__c by >$10,000 — show both labeled clearly

# ─── FEATURE 7: LEGAL / LITIGATION HOLD CHECK ────────────────────────────────

LEGAL_CHECK_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       X3rd_Party_Collections__c, Strategic_Account__c,
       Strategic_Account_Child__c, Stop_Hold_Override__c,
       Legal_Notes__c,
       (SELECT Id, Subject, Status, Type
        FROM Cases WHERE IsClosed = false
          AND (Type = 'Legal'
            OR Subject LIKE '%settlement%'
            OR Subject LIKE '%litigation%'
            OR Subject LIKE '%legal%'
            OR Subject LIKE '%attorney%'
            OR Subject LIKE '%bankruptcy%'))
FROM Account
WHERE Name IN ({account_names})
  AND IsDeleted = false
LIMIT 50
"""
# Returns: CLEAR / BLOCKED / REVIEW FLAG per account
# BLOCKED:      Account_Litigation_Hold__c = true OR Bankruptcy_Hold__c = true
# REVIEW FLAG:  Legal_Notes__c contains keywords (litigation, attorney, bankruptcy,
#               legal hold, settlement, lawsuit, counsel)
# This query gates Features 1 and 11 — run it first

# ─── FEATURE 8: PAYMENT PLAN RISK REVIEW ─────────────────────────────────────

# Branch A — specific account named
PAYMENT_PLAN_SPECIFIC_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Stop_Hold_Override__c, Finance_Hold_Status__c,
       Legal_Notes__c, CSM_Name_Text__c, Billing_Email_s__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 5)
FROM Account
WHERE Name LIKE '%{account_name}%'
  AND IsDeleted = false
LIMIT 5
"""

# Branch B — portfolio scan (no account named)
PAYMENT_PLAN_PORTFOLIO_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Stop_Hold_Override__c, Legal_Notes__c, CSM_Name_Text__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 3)
FROM Account
WHERE Total_Overdue_Balance__c > 0
  AND IsDeleted = false
ORDER BY Total_Overdue_Balance__c DESC
LIMIT 100
"""

# ─── FEATURE 10: CUSTOMER STATUS SUMMARY ─────────────────────────────────────

CUSTOMER_SUMMARY_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Stop_Hold_Override__c, Bankruptcy_Hold__c, Account_Litigation_Hold__c,
       Legal_Notes__c, X3rd_Party_Collections__c, Strategic_Account__c,
       CSM_Name_Text__c, Billing_Email_s__c,
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 5),
       (SELECT Id, Subject, Status, Type, CreatedDate, Description
        FROM Cases WHERE IsClosed = false ORDER BY CreatedDate DESC LIMIT 10)
FROM Account
WHERE Name LIKE '%{account_name}%'
  AND IsDeleted = false
LIMIT 5
"""

# ─── FEATURE 11: DEMAND LETTER ───────────────────────────────────────────────

DEMAND_LETTER_ACCOUNT_QUERY = """
SELECT Id, Name, Total_Overdue_Balance__c, Days_Overdue__c,
       Open_Balance__c, SCG_Active_ARR__c, Support_Hold__c,
       Bankruptcy_Hold__c, Account_Litigation_Hold__c, Legal_Notes__c,
       X3rd_Party_Collections__c, CSM_Name_Text__c, Billing_Email_s__c,
       (SELECT Id, Subject, Status, Type, CreatedDate
        FROM Cases WHERE IsClosed = false ORDER BY CreatedDate DESC LIMIT 5),
       (SELECT Id, Name, StageName, CloseDate, Amount
        FROM Opportunities WHERE IsClosed = false ORDER BY CloseDate ASC LIMIT 3)
FROM Account
WHERE Name LIKE '%{account_name}%'
  AND IsDeleted = false
LIMIT 5
"""
# Feature 7 must run FIRST — BLOCKED accounts never receive demand letters
# REVIEW FLAG accounts require Jordan Duke approval before demand letter is drafted
