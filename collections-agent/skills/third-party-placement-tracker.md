# Skill — Third-Party Placement Tracker

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `third-party-placement-tracker` |
| Display Name | third-party-placement-tracker |
| Short Description | Review 60+ DPD accounts for placement. |
| Trigger Description | Use when the user asks to review Salesforce accounts 60+ days past due for third-party placement, exclude blocked accounts, flag legal-note review items, and draft the internal CSM/AM review email. |
| Default Prompt | Use $third-party-placement-tracker to review Salesforce accounts for third-party placement eligibility, flag legal-note review items, and draft the internal review email. |

---

## Purpose

Use this skill when the request is to build a third-party placement review set from Salesforce, separate blocked accounts from workable accounts, surface legal or settlement review flags from note text, and draft the internal review email.

---

## Request Shapes

Use this skill for requests like:
- "Review all accounts 60+ days past due for third-party placement and draft the review email."
- "Build the placement tracker, exclude blocked accounts, and flag any legal-note hits."
- "Give me the eligible accounts, excluded accounts with reasons, and the CSM/AM review draft for placement."

---

## Required Tooling

**Advantive Salesforce** — source for the account set and blocking fields.

---

## Workflow

### Step 1 — Query Salesforce

Query Salesforce for accounts with `Days_Overdue__c >= 60`.

Retrieve the minimum fields needed to classify each account:
- `Id`
- `Name`
- `Total_Overdue_Balance__c`
- `Open_Balance__c`
- `Days_Overdue__c`
- `Support_Hold__c`
- `CSM_Name_Text__c`
- `Legal_Notes__c`
- `Bankruptcy_Hold__c`
- `Account_Litigation_Hold__c`
- `X3rd_Party_Collections__c`
- `Strategic_Account__c`
- `Strategic_Account_Child__c`
- `Stop_Hold_Override__c`

### Step 2 — Apply Exclusion Rules

Exclude any account from the eligible list if one or more of these blocking conditions are true:
- `Bankruptcy_Hold__c = true`
- `Account_Litigation_Hold__c = true`
- `X3rd_Party_Collections__c = true`
- `Strategic_Account__c = true`
- `Strategic_Account_Child__c = true`
- `Stop_Hold_Override__c = true`

For each excluded account, preserve every matching exclusion reason. Do not collapse multiple reasons into one generic label.

### Step 3 — Legal Notes Scan

For each remaining non-blocked account, scan `Legal_Notes__c` for these keywords and phrases:

`settlement`, `settlement agreement`, `settled`, `walkaway`, `walk away`, `walked away`, `legal hold`, `litigation`, `breach`, `dispute`, `termination notice`, `attorney`, `lawsuit`, `do not contact`, `cease and desist`, `bankruptcy`, `remediation`

- Treat keyword matches as **review flags**, not automatic blockers, unless the account is already blocked by the structured exclusion fields above.
- When a legal-note keyword hit exists, quote the exact matching text or the smallest useful excerpt that contains the hit.

### Step 4 — Build Output

After retrieving results, state the total account count returned by Salesforce.

At the top of every output, include this note exactly:
> `YayPay not connected — outreach attempt count unverified. Rep must confirm contact attempt history manually before submitting to TAA.`

Before the CSM-grouped eligible list, include a one-line balance distribution summary:
> `$[X]k+ overdue: [N] accounts | $[Y]k–$[X]k: [N] accounts | Under $[Y]k: [N] accounts`

### Step 5 — Group by CSM

Group eligible accounts by `CSM_Name_Text__c`.

At the start of each CSM group, show:
> `CSM: [Name] — [N] accounts — Total Overdue: $[sum of Total_Overdue_Balance__c]`

Sort CSM buckets by total overdue balance descending.

After listing each CSM bucket, calculate:
- Total on-hold balance = sum of `Total_Overdue_Balance__c` where `Support_Hold__c = true`
- Hold concentration % = on-hold balance / bucket total

If hold concentration is greater than 50%, add exactly:
> `HOLD CONCENTRATION: $[amount] ([X]%) of this CSM's eligible balance is on active support hold. Placement alongside multiple holds requires coordinated approach — confirm strategy with rep and Jordan Duke before sending CSM review email.`

If a CSM bucket total does not match the sum of the visible account balances, flag exactly:
> `Multi-currency mismatch detected — bucket total may be incomplete. Verify full account list directly in Salesforce before sending CSM email.`

Do not silently accept a rollup total that is lower than any single account balance in the same bucket.

### Step 6 — Account Row Rules

Within each CSM bucket, sort accounts by `Total_Overdue_Balance__c` descending.

Every eligible account row must show:
> `Account Name | Total_Overdue_Balance__c | Days_Overdue__c | Support_Hold__c | CSM`

If `Support_Hold__c = true`, add:
> `ON HOLD — placement alongside active hold; confirm approach with rep.`

If `Days_Overdue__c > 365`, add:
> `EXTREME DPD — [X] days ([Y] years). Verify invoice date accuracy before placement submission. May be a data quality issue or write-off candidate instead.`

If `Days_Overdue__c > 1000`, also flag as high priority for data review before TAA submission.

### Step 7 — Unassigned Accounts

Treat `CSM_Name_Text__c = null`, blank, or `CSM Pool` as unassigned.

For unassigned eligible accounts, add:
> `These [N] accounts require CSM assignment before review email can be sent. Recommend: route to Jordan Vasquez for ownership assignment.`

### Step 8 — Draft the Review Email

Draft the internal CSM/AM review email with a clear 7-day response window. The email should:
- Explain that the listed accounts are being reviewed for third-party placement
- Ask recipients to reply with objections or relevant context within 7 calendar days
- State that silence after the 7-day window will be treated as no objection
- Avoid claiming any account has already been placed

If account-level AM or recipient details are not available, draft the email body anyway and clearly label any recipient gaps.

---

## Output Contract

Always return these sections in this order:

### 1. Eligible Accounts
Start with:
- Total returned account count
- Required YayPay gap note
- One-line balance distribution summary

Then present eligible accounts grouped by CSM. For each CSM bucket include:
- `CSM: [Name] — [N] accounts — Total Overdue: $[sum]`
- Hold concentration calculation summary
- Hold concentration warning if on-hold balance exceeds 50% of bucket total
- Multi-currency mismatch warning if bucket total doesn't match visible-row sum

For each eligible account include:
- `Account Name | Total_Overdue_Balance__c | Days_Overdue__c | Support_Hold__c | CSM`
- Hold note when applicable
- Extreme-DPD flag when applicable
- Short placement-readiness note

### 2. Excluded Accounts With Reasons
For each excluded account include:
- Account name
- Every exclusion reason triggered by the blocking fields
- The field names or field meaning that caused the exclusion

### 3. Legal Review Flags
For each flagged account include:
- Account name
- Matched keyword or phrase
- Exact matching text or excerpt from `Legal_Notes__c`
- Short note that human review is required before placement

### 4. CSM/AM Review Email Draft
Return a complete internal draft with:
- Subject line
- Recipient placeholder or resolved recipients when available
- Concise body
- Explicit 7-day response deadline language

---

## Quality Bar

- Do not invent account facts, recipient names, or legal conclusions.
- Do not mark a legal-note keyword hit as a full block unless a structured blocking field also supports exclusion.
- Do not include excluded accounts in the eligible list.
- Do not output a name-only eligible list.
- Do not ignore bucket-total mismatches when the visible balances suggest a multi-currency or rollup issue.
- If no accounts qualify for a section, say so explicitly instead of omitting the section.
- Keep the email operational and concise.
