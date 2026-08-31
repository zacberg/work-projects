"""
AR Collections Agent — Email and Output Templates
Confirmed structures for all outbound communications.
Upload this file to the ChatGPT agent knowledge base as authoritative reference.
"""

# ─── FEATURE 1: CSM / AM REVIEW EMAIL (PRE-PLACEMENT) ────────────────────────

PLACEMENT_CSM_EMAIL_SUBJECT = "Action Required: Collections Review — {account_name}"

PLACEMENT_CSM_EMAIL_BODY = """Hi {csm_name},

I wanted to give you a heads-up before we move forward with third-party placement on the account(s) below. Please review and let me know if there are any outstanding conversations or renewal activities we should be aware of before we proceed.

**Account(s) for Review:**

{account_table}
(Account | Balance | Days Past Due | Last CSM Activity)

We are targeting a decision within 7 business days. If we don't hear back by {deadline_date}, we will proceed with placement.

Please reach out if you have any questions or need additional context.

Thanks,
{rep_name}
AR Collections | Advantive
"""
# {account_table} = one row per account: Name | Total_Overdue_Balance__c | Days_Overdue__c | last activity
# {deadline_date} = today + 7 business days
# Group all accounts for a single CSM into one email — do not send one email per account

# ─── FEATURE 3: CASH UPDATE EMAIL ────────────────────────────────────────────

CASH_UPDATE_SUBJECT = "DELIVERY | Collections Forecast as of {date}"

CASH_UPDATE_BODY = """Hi team,

Please see today's collections update below.

**Cash Collected (MTD):** ${cash_collected}
**Monthly Target:** ${target}
**Variance to Target:** ${variance} ({variance_pct}%)

**Collections PEQs**
• Promise to Pay: {ptp_amount} [MANUAL — YayPay not connected]
• Checks in Transit: {checks_in_transit}  [TUESDAY ONLY — source: Josh Snow, Teams]
• Expected Cash This Week: {expected_cash}

**>60 Day Balance**
Total: ${overdue_60_balance}

Top accounts:
{overdue_account_table}
(Account | Balance | Days Past Due | Hold Status)

{path_to_target_section}

{rep_name}
AR Collections | Advantive
"""

CASH_UPDATE_PATH_TO_TARGET = """
**Path to Target**
• Remaining gap: ${gap}
• Key accounts expected to clear: {key_accounts}
"""
# FRIDAY RULE: suppress Path to Target section entirely — do not include the block above
# TUESDAY RULE: include Checks in Transit line with Josh Snow as source
# PTP always placeholder until YayPay is connected

# ─── FEATURE 4: PRE-DRAFT CHECK SUMMARY HEADER ───────────────────────────────

EMAIL_PREDRAFT_HEADER = """
--- Pre-Draft Check Summary ---
Legal (F7):           {legal_result}
Stop_Hold_Override:   {override_result}
Active deals:         {deals_result}
NetSuite caution:     {netsuite_result}
Prior outreach:       {outlook_result}
YayPay dunning:       Status unknown — rep should confirm before sending
--------------------------------
"""
# Always output this block before the draft email
# legal_result:   CLEAR / BLOCKED / REVIEW FLAG
# override_result: NONE or "TRUE — confirm collection approach with rep"
# deals_result:   NONE or "[Opp Name] — [Stage] — closes [Date] — $[Amount]"
# netsuite_result: CLEAR / FLAGGED / "Not checked this session — verify manually"
# outlook_result:  summary of recent emails or "Outlook inaccessible this session"

# ─── FEATURE 11: DEMAND LETTER ────────────────────────────────────────────────

DEMAND_LETTER_SUBJECT = "FINAL NOTICE: Outstanding Balance Due — {account_name}"

DEMAND_LETTER_BODY = """
[Date]

{account_name}
{billing_contact}

Re: Outstanding Balance — FINAL NOTICE

Dear {contact_name},

This letter serves as formal notice that your account with Advantive carries an
outstanding balance of ${overdue_balance}, now {days_overdue} days past due.

Despite previous communications dated {prior_outreach_dates}, we have not received
payment or a confirmed payment arrangement.

**Immediate Action Required:**
Full payment of ${overdue_balance} must be received within 10 business days of this
notice, by {deadline_date}.

Failure to remit payment or contact us to arrange a resolution by this date will
result in referral to third-party collections and potential termination of service.

To resolve this matter, contact {ar_rep_name} at {ar_rep_email} or
receivables@advantive.com.

Sincerely,
{ar_rep_name}
Senior Manager, Accounts Receivable
Advantive Collections
{ar_rep_email}
(656) 444-9887
"""
# Feature 7 must return CLEAR before this template is used
# Jordan Duke confirmed phone: (656) 444-9887 — source: SF case 01629175 email signature
# REVIEW FLAG accounts require Jordan Duke approval before drafting
# BLOCKED accounts: do not draft, surface the litigation/bankruptcy flag

# ─── AGENT IMPROVEMENT NOTE (SELF-IMPROVEMENT PROTOCOL) ──────────────────────

IMPROVEMENT_NOTE_TEMPLATE = """
=== Agent Improvement Note — {date} ===

Session summary: {session_topic}

Manual inputs required this session:
{manual_inputs}

Data gaps encountered:
{data_gaps}

Low-confidence sections:
{low_confidence}

Suggested instruction additions:
{instruction_additions}

Suggested knowledge file additions:
{knowledge_file_additions}

Corrections received from user:
{corrections}

Recurring gaps (seen in 2+ sessions):
{recurring_gaps}
===========================================
"""
# Always produce this note at the end of every session
# If a field has nothing to report, write "None" — do not omit the field
