# Skill — Demand and Termination Letters

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `demand-and-termination-letters` |
| Display Name | demand-and-termination-letters |
| Short Description | Draft formal demand and termination letters. |
| Trigger Description | Use when the user asks to draft a formal demand or termination letter, but only after running settlement and legal exclusion screening and excluding accounts with settlement, walkaway, litigation-hold, or restricted-contact evidence. |
| Default Prompt | Use $demand-and-termination-letters to run legal exclusion screening, review account context, and draft a formal demand or termination letter. |

---

## Purpose

Use this skill when the request is to draft a formal demand or termination letter for delinquent accounts, after first screening out accounts that should not receive the letter because of settlement, walkaway, litigation, or restricted-contact concerns.

---

## Request Shapes

Use this skill for requests like:
- "Draft a demand letter for this delinquent account."
- "Review these accounts for legal blockers, then draft termination letters for the eligible ones."
- "Prepare a formal collections letter with the right deadline and placeholders for missing details."

---

## Required Tooling

| Source | Purpose |
|--------|---------|
| Advantive Salesforce | Account name, overdue balance, days past due, billing email, legal notes, and invoice context |
| `settlement-and-legal-exclusion-check` | Required pre-check before drafting any letter |
| NetSuite SB1 | Open invoice retrieval for invoice line population |

---

## Workflow

### Step 1 — Run Legal Pre-Check (Required)

Always run the `settlement-and-legal-exclusion-check` first on the target account set.

Do **not** draft any demand or termination letter for accounts with any of these findings:
- Settlement agreement evidence
- Walkaway evidence
- Active litigation hold
- Restricted-contact note evidence (`do not contact`, `cease and desist`)

If the pre-check returns `Blocked` or shows any of those disqualifying findings, stop letter drafting for that account and return the blocking evidence instead.

### Step 2 — Retrieve Salesforce Context (Eligible Accounts Only)

For eligible accounts, retrieve:
- Account name
- Overdue balance
- Days past due
- Billing email
- `CSM_Name_Text__c`
- `X3rd_Party_Collections__c`
- Legal notes
- Invoice context

### Step 3 — Retrieve Invoice Data from NetSuite

Before drafting, attempt to retrieve open invoices from NetSuite SB1 for the target account.

- If NetSuite returns invoice data, populate invoice lines with the actual invoice numbers and amounts returned.
- If NetSuite is unavailable or returns no match, state exactly:
> `Invoice detail unavailable — NetSuite not queried or no match found. Rep must pull invoice list from NetSuite manually before sending.`

### Step 4 — CSM Coordination Line

Retrieve `CSM_Name_Text__c` for the account and include one of these lines in the `What We Should Do Next` section:

If CSM is available:
> `CSM coordination required: [CSM Name] must be notified before this letter is sent. Collections and CSM need one aligned position.`

If CSM is null, blank, or unavailable:
> `No CSM assigned — route to Jordan Duke for ownership confirmation before sending.`

### Step 5 — Placement Cross-Reference

If `Days_Overdue__c >= 60` and `X3rd_Party_Collections__c = false`, include:
> `Placement check: This account is eligible for Feature 1 placement with TAA. Confirm whether placement was already attempted before sending demand letter. If not, consider whether demand letter and placement should be coordinated.`

### Step 6 — Draft the Letter

Draft either a formal demand letter or a formal termination letter depending on the user's request or workflow context.

**Rules:**
- Use a **30 calendar day** payment deadline in every draft
- Replace vague `additional collection measures` phrasing with exactly:
> `If payment or written response is not received by [deadline], Advantive reserves the right to refer this account to third-party collections and to initiate contract termination proceedings per the terms of your agreement.`
- Also add when that language is used:
> `Confirm final language with Jordan Duke before first live send — legal/standard language may differ from this template.`
- Leave placeholders for missing AP or billing contact names, and any invoice detail unavailable after the NetSuite attempt
- Flag these as open items that still need confirmation before sending: delivery method, final termination closing language
- Keep the letter formal, operational, and clearly marked as a draft — do not present it as already sent

### Step 7 — Signature Block

Never generate, estimate, or use a placeholder phone number in any signature block.

Use this signature format for Jordan Duke exactly unless a connected system or attached knowledge file confirms additional details:

```
Jordan Duke
Senior Manager, Accounts Receivable
Advantive Collections
jordan.duke@advantive.com
```

---

## Output Contract

Always return these sections in this order:

### 1. Pre-Check Result
For each account include:
- Settlement and legal exclusion result
- Blocking evidence when present
- Whether letter drafting is allowed

### 2. Retrieved Letter Inputs
For each eligible account include:
- Account name
- Overdue balance
- Days past due
- Billing email
- CSM name
- Placement-check status when applicable
- Relevant legal-note context
- Invoice context retrieved from Salesforce and/or NetSuite
- The explicit NetSuite invoice-data gap note when no invoice match is available
- Any missing fields that will remain placeholders

### 3. Letter Draft
Return the full draft letter with:
- Letter type
- Recipient line with placeholders where needed
- Account-specific facts
- 30-day payment deadline
- Jordan Duke signature with no phone number unless explicitly confirmed by retrieved data
- The required closing-threat language
- Placeholders only for still-missing AP contact or invoice details
- A `What We Should Do Next` section with the required CSM coordination line and placement cross-reference when applicable

### 4. Open Items Before Sending
Always list:
- Delivery method still needs confirmation
- Final termination closing language still needs confirmation
- Confirm final escalation language with Jordan Duke before first live send
- Any remaining missing recipient or invoice details

---

## Quality Bar

- Never draft a letter for an account blocked by settlement, walkaway, active litigation hold, or restricted-contact evidence.
- Do not invent AP contacts, invoice details, or legal conclusions.
- Never generate or estimate a phone number for Jordan Duke or anyone else.
- Keep the legal-exclusion evidence visible in the output when drafting is blocked.
- Keep the letter formal and ready for internal review, not as a sent communication.
- If no eligible accounts remain after the pre-check, say so explicitly and do not output a letter draft.
