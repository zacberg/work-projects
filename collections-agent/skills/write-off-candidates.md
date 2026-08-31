# Skill — Write-Off Candidates

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `write-off-candidates` |
| Display Name | write-off-candidates |
| Short Description | Review aged balances for write-off candidacy. |
| Trigger Description | Use when the user asks to review Salesforce accounts 90+ days past due for write-off candidacy, exclude accounts already in the decommission pipeline, flag legal-note review items, draft per-account write-off rationales, and prepare the Billing Ops handoff. |
| Default Prompt | Use $write-off-candidates to review aged accounts for write-off candidacy, flag legal-note review items, and draft the Billing Ops handoff. |

---

## Purpose

Use this skill when the request is to identify aged-balance write-off candidates from Salesforce, remove decommission-pipeline accounts from the candidate set, surface legal or settlement review flags, and prepare the internal write-off handoff.

---

## Request Shapes

Use this skill for requests like:
- "Review all 90+ day past due accounts for write-off candidacy and draft the handoff."
- "Find aged accounts that could be written off, excluding decommission accounts and flagging legal-note issues."
- "Build the write-off candidate list with rationales and a Billing Ops handoff draft."

---

## Required Tooling

**Advantive Salesforce** — source for overdue balance, days past due, lifecycle status, and legal-note context.

---

## Workflow

### Step 1 — Query Salesforce

Query Salesforce for accounts where **all** of these are true:
- `Days_Overdue__c >= 90`
- `Total_Overdue_Balance__c > 0`

Retrieve the minimum fields needed to classify each account:
- `Id`
- `Name`
- `Total_Overdue_Balance__c`
- `Open_Balance__c`
- `Days_Overdue__c`
- `Support_Hold__c`
- `Type`
- `Customer_to_Former_Customer_Date__c` (when available)
- `Bankruptcy_Hold__c`
- `Account_Litigation_Hold__c`
- `Legal_Notes__c`
- `CSM_Name_Text__c`

### Step 2 — Exclude Decommission-Pipeline Accounts

Exclude any account already in the decommission pipeline from the write-off candidate list.

Treat these lifecycle signals as decommission-pipeline evidence when available:
- `Type = Former Customer`
- `Type = Out of Business`
- Other explicit lifecycle or decommission workflow markers returned by the current query

If decommission-pipeline state cannot be confirmed from the available fields, say so explicitly and classify that as a data gap rather than assuming the account is eligible.

### Step 3 — Legal Notes Scan

Run the canonical legal and settlement keyword scan against `Legal_Notes__c` for the remaining non-decommissioned accounts:

`settlement`, `settlement agreement`, `settled`, `walkaway`, `walk away`, `walked away`, `legal hold`, `litigation`, `breach`, `dispute`, `termination notice`, `attorney`, `lawsuit`, `do not contact`, `cease and desist`, `bankruptcy`, `remediation`

- Treat legal-note keyword matches as **review flags**, not automatic write-off approval or denial
- Also surface any structured `Bankruptcy_Hold__c` or `Account_Litigation_Hold__c` fields separately
- For every keyword hit, quote the exact matching text or the smallest useful excerpt that contains the hit

### Step 4 — Apply Hold Flags

For every write-off candidate row, always include hold status formatted exactly as:
- `Hold: ON HOLD` when `Support_Hold__c = true`
- `Hold: No hold` when `Support_Hold__c = false` or null

If `Support_Hold__c = true`, add exactly:
> `Hold in place — confirm with rep whether active collections discussion is ongoing before routing for write-off approval.`

### Step 5 — Approval Tier Rules

When presenting write-off approval tiers, use Salesforce User titles as authoritative over SOP-document titles.

For the `$25k–$50k` band approver, always use:
> `Joy Jones (Controller) — joy.jones@advantive.com`

Always add this confidence note anywhere the approval tier breakdown is presented:
> `Approval thresholds based on SOP approval matrix — confirm tier breakpoints with Jordan Duke (jordan.duke@advantive.com) before first routing batch.`

### Step 6 — JMCFS Special Note

If JMCFS appears in the write-off review, add this note:
> `Legal_Notes__c on JMCFS appears to be a renewal logistics note — not a legal restriction. Confirm with CSM John Evans before write-off submission.`

### Step 7 — Draft Write-Off Rationales

Draft a concise write-off rationale for each candidate account explaining:
- Why the account meets the aged-balance threshold
- Whether the account is excluded from decommission handling
- Any legal, settlement, bankruptcy, or litigation review concerns
- What still needs human review before approval

### Step 8 — Draft Billing Ops Handoff

Prepare a Billing Ops handoff draft addressed to Tiffany Johnson for the final candidate set.

The handoff draft must clearly state that **all write-offs require approval from both Jordan Duke and Justin Wixom** before any action is taken. Do not present any write-off as approved, executed, or ready for system action without those approvals.

---

## Output Contract

Always return these sections in this order:

### 1. Write-Off Candidates
For each candidate account include:
- Account name
- Days past due
- Overdue balance
- Open balance when available
- Hold status
- Short write-off rationale
- Hold note when applicable

### 2. Excluded Decommission-Pipeline Accounts
For each excluded account include:
- Account name
- Decommission-pipeline reason
- Source field or lifecycle evidence used for the exclusion

### 3. Legal or Settlement Review Flags
For each flagged account include:
- Account name
- Matched keyword or structured legal flag
- Exact matching text or excerpt when `Legal_Notes__c` caused the flag
- Short note on why human review is needed

### 4. Billing Ops Handoff Draft
Return a complete internal draft addressed to Tiffany Johnson that includes:
- Subject line
- Concise summary of the candidate set
- Notable exclusions or legal-review concerns
- Explicit reminder that Jordan Duke and Justin Wixom must both approve before any write-off action
- The approval-tier confidence note

### 5. Summary and Recommended Next Actions
Provide:
- Total candidate count
- Total excluded decommission-pipeline count
- Total legal-review-flag count
- Highest-priority next actions
- Any data gaps that limit confidence in the candidate set

---

## Quality Bar

- Do not invent lifecycle state, approval status, or legal conclusions.
- Do not omit hold status from any write-off candidate row.
- Do not include decommission-pipeline accounts in the final candidate list.
- Do not treat legal-note keyword hits as automatic disqualifiers unless structured fields also support that conclusion.
- Use Salesforce User title data as authoritative when naming approvers and titles.
- If no accounts qualify for a section, say so explicitly instead of omitting the section.
- Keep the Billing Ops handoff operational and concise.
