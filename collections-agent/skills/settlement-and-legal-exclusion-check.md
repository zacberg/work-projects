# Skill — Settlement and Legal Exclusion Check

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `settlement-and-legal-exclusion-check` |
| Display Name | Settlement and Legal Exclusion Check |
| Short Description | Screen accounts for settlement and legal blockers. |
| Trigger Description | Use when the user asks to screen a list of accounts for settlement agreements, walkaways, legal escalations, prior agency placement, open legal or dispute cases, and legal-note keyword hits, then return Clear, Blocked, or Review Flag with evidence. |
| Default Prompt | Use $settlement-and-legal-exclusion-check to review accounts for settlement, legal, dispute, and placement-blocking issues and return Clear, Blocked, or Review Flag results. |

---

## Purpose

Use this skill when the request is to screen one or more accounts for legal, settlement, dispute, or prior-placement issues before downstream collections action.

---

## Request Shapes

Use this skill for requests like:
- "Run a settlement and legal exclusion check on these accounts."
- "Tell me which accounts are blocked, clear, or only need review before placement."
- "Screen this account list for settlement, walkaway, legal, dispute, and prior agency issues."

---

## Required Tooling

**Advantive Salesforce** — primary source for account-level legal fields, prior agency placement state, legal notes, and related open case context.

---

## Workflow

### Step 1 — Resolve Account List

Accept a user-provided list of accounts. If the list contains names only, resolve them to the smallest reliable Salesforce account set before proceeding.

### Step 2 — Retrieve Screening Fields

For each account, retrieve the smallest useful field set needed for screening:
- `Id`
- `Name`
- `Legal_Notes__c`
- `Bankruptcy_Hold__c`
- `Account_Litigation_Hold__c`
- `X3rd_Party_Collections__c`
- Any settlement, walkaway, or dispute-related structured fields returned by the current query path

Use related Salesforce case retrieval when needed to determine whether the account has an open legal or dispute case.

### Step 3 — Check for Evidence Types

For each account, check for these evidence types:
- Settlement agreements
- Walkaways
- Legal escalations
- Prior agency placement
- Open legal or dispute cases
- Legal-note keyword hits

### Step 4 — Legal Keyword Scan

Use this exact keyword list when scanning `Legal_Notes__c` or closely related note text:

`settlement`, `settlement agreement`, `settled`, `walkaway`, `walk away`, `walked away`, `legal hold`, `litigation`, `breach`, `dispute`, `termination notice`, `attorney`, `lawsuit`, `do not contact`, `cease and desist`, `bankruptcy`, `remediation`

For every keyword hit, quote the exact matching text or the smallest useful excerpt that contains the hit.

### Step 5 — Classify Each Account

| Status | Criteria |
|--------|----------|
| **Blocked** | Structured evidence supports settlement, walkaway, legal escalation, prior agency placement, bankruptcy, litigation hold, or an open legal or dispute case |
| **Review Flag** | The only evidence is one or more legal-note keyword hits with no structured blocking field or open-case evidence |
| **Clear** | No blocking or review evidence is found |

If an account has both structured blocking evidence and legal-note hits, keep the final status as `Blocked` and include all evidence found.

Do not escalate a note-only keyword hit to `Blocked` without structured support.

### Step 6 — Settlement Review Flag

If settlement or walkaway evidence is found, explicitly flag the account for **Gaby Vitoria** to review before the weekly settlement meeting.

---

## Output Contract

Return one result per account. For each account include:
- Account name
- Final status: `Clear`, `Blocked`, or `Review Flag`
- Every evidence item found
- Source field or source record type for each evidence item
- Exact matching text or excerpt for any legal-note hit
- Recommended next action

After the per-account list, include a **Settlement Review Follow-Up** section that lists every account flagged for Gaby Vitoria review before the weekly settlement meeting.

---

## Quality Bar

- Do not invent legal conclusions, case state, or settlement status.
- Do not mark an account as `Blocked` when the only evidence is a legal-note keyword hit.
- Include every evidence item found, not just the first one.
- If no evidence is found for an account, still return it as `Clear` with a brief note.
- Keep the recommended next action concise and operational.
