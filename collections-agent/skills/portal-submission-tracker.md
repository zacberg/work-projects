# Skill — Portal Submission Tracker

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `portal-submission-tracker` |
| Display Name | portal-submission-tracker |
| Short Description | Track portal, tax, and billing submission cases. |
| Trigger Description | Use when the user asks to review open Salesforce cases for portal uploads, tax documents, invoice submissions, vendor portals, purchase orders, or billing, flag stale cases, categorize blockers, and draft the Billing Ops handoff email. |
| Default Prompt | Use $portal-submission-tracker to review open portal and billing submission cases, flag stale items, and draft the Billing Ops handoff email. |

---

## Purpose

Use this skill when the request is to review open portal and billing submission cases from Salesforce, separate them into action buckets, flag stale items, and prepare a Billing Ops handoff for Tiffany Johnson.

---

## Request Shapes

Use this skill for requests like:
- "Review open portal submission cases and tell me what is stale or blocked."
- "Build the portal submission tracker with pending, rejected, and tax-document categories."
- "Summarize portal and billing cases, then draft the Billing Ops escalation email for stale items."

---

## Required Tooling

**Advantive Salesforce** — source for open case status, age, recent activity, and category evidence.

---

## Workflow

### Step 1 — Query Salesforce

Query Salesforce for open cases related to one or more of these topics:
- Portal uploads
- Tax documents
- Invoice submissions
- Vendor portals
- Purchase orders
- Billing

Retrieve the smallest useful field set needed to classify and age the cases:
- `Id`
- `CaseNumber` (when available)
- `Subject`
- `Status`
- `Type`
- `Priority`
- `CreatedDate`
- `LastModifiedDate`
- `LastActivityDate` (when available)
- `OwnerId`
- `Owner.Name`
- `Description`
- `Account.Name`
- `Account.Total_Overdue_Balance__c`
- `Account.Days_Overdue__c`
- `Account.Open_Balance__c`
- `Account.Support_Hold__c`
- `Account.X3rd_Party_Collections__c`

A case is in scope when the subject, description, or case typing clearly points to portal upload work, tax-document work, invoice submission issues, vendor portal issues, purchase-order gating, or billing workflow.

### Step 2 — Run Legal Screening

Before outputting results, run the settlement and legal exclusion screening from the `settlement-and-legal-exclusion-check` workflow on every account in scope. Classify each one as `CLEAR`, `BLOCKED`, or `REVIEW FLAG`.

### Step 3 — Apply Hold and Placement Flags

For every in-scope case row, always include hold status from `Account.Support_Hold__c`:
- `Hold Status: ON HOLD` when true
- `Hold Status: No hold` when false or null

If `Account.Support_Hold__c = true` and the case is a billing dispute, add exactly:
> `Hold already applied — billing resolution may be required to lift hold. Cross-reference Feature 2 before rep action.`

If all of the following are true, add this flag and keep the account in the billing case list:
- `Account.Days_Overdue__c >= 60`
- `Account.Support_Hold__c = false`
- `Account.X3rd_Party_Collections__c = false`

> `PLACEMENT ELIGIBLE — [DPD] DPD, no hold, not in third-party. Flag for Feature 1 review.`

### Step 4 — Categorize Cases

Categorize each in-scope case into exactly one primary bucket:

| Bucket | Criteria |
|--------|----------|
| Pending Submission | Cases awaiting upload, submission, correction, or normal processing |
| Rejected or Blocked | Cases where portal, customer requirements, missing data, rejection, or billing dependency is actively preventing completion |
| Missing Tax Documents | Cases primarily blocked by W-9, W-8, tax certificate, exemption, or related documentation gaps |

### Step 5 — Flag Stale Cases

Flag a case as stale when **both** are true:
- The case is older than 5 business days
- There has been no meaningful activity in the last 5 business days

Use `LastActivityDate` as the preferred activity signal. If unavailable, use `LastModifiedDate` as the fallback. Count business days by excluding weekends. If holiday-calendar certainty is unavailable, note that the stale check excludes weekends but may not reflect holidays.

Treat these as escalation signals even when a case is not technically stale:
- Repeated rejection or resubmission loops
- Missing customer tax documentation that prevents invoice progression
- Purchase-order or vendor-portal requirements blocking payment timing
- High-priority billing cases with aged balances or material overdue exposure

### Step 6 — Case Row Format

Use this row format in all case lists:
> `Account | Balance | DPD | Case # | Status | Last Modified | Hold | Legal | Owner | Flag`

- `Legal` must display one of: `CLEAR`, `BLOCKED`, `REVIEW FLAG`
- `Flag` should contain the most important applicable note — if more than one flag applies, lead with the higher-risk blocker first
- When `Status = 'Assigned'`, include `OwnerId` and `Owner.Name`
- If owner information is missing, state: `Owner: not retrieved — rep should check in SF`

### Step 7 — Draft Billing Ops Handoff Email

Draft a Billing Ops handoff email to Tiffany Johnson for any case that is stale or meets escalation criteria. The email should:
- Summarize the stale or escalated cases
- State why each case needs Billing Ops review
- Highlight overdue-balance impact when available
- Ask for next-step ownership or unblock guidance

---

## Output Contract

Always return these sections in this order:

### 1. Pending Submission
For each case include:
- `Account | Balance | DPD | Case # | Status | Last Modified | Hold | Legal | Owner | Flag`
- Short issue summary
- Latest activity date used
- Recommended next action

### 2. Rejected or Blocked
For each case include:
- `Account | Balance | DPD | Case # | Status | Last Modified | Hold | Legal | Owner | Flag`
- Blocking reason
- Latest activity date used
- Recommended next action

### 3. Missing Tax Documents
For each case include:
- `Account | Balance | DPD | Case # | Status | Last Modified | Hold | Legal | Owner | Flag`
- Missing document type or tax issue
- Latest activity date used
- Recommended next action

### 4. Stale or Escalation Cases
Include only cases that are stale or need Billing Ops review. For each one include:
- `Account | Balance | DPD | Case # | Status | Last Modified | Hold | Legal | Owner | Flag`
- Why it is stale or escalated
- Evidence used for the stale determination
- Recommended Billing Ops follow-up

### 5. Billing Ops Handoff Email Draft
Return a complete internal draft addressed to Tiffany Johnson that includes:
- Subject line
- Concise summary of stale or escalation cases
- Per-case reason for handoff
- Ask for next steps or ownership confirmation

### 6. Summary and Recommended Next Actions
Provide:
- Total case counts by category
- Stale-case count
- The highest-priority next actions
- Any data gaps that limit the review

---

## Quality Bar

- Do not invent activity dates, case statuses, or portal outcomes.
- Do not skip the legal-screening result, hold status, or owner field in the case row.
- Do not classify a case into multiple primary buckets — choose the dominant blocker.
- Clearly label when stale logic used `LastModifiedDate` instead of `LastActivityDate`.
- If no cases qualify for a category, say so explicitly instead of omitting the section.
- Keep the Billing Ops handoff concise and actionable.
