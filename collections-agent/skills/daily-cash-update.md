# Skill — Daily Cash Update

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `daily-cash-update` |
| Display Name | daily-cash-update |
| Short Description | Draft the daily leadership cash forecast email. |
| Trigger Description | Use when the user asks to build the daily collections forecast, pull aging and tracker inputs, calculate the Go Get number for the current weekday, and draft the leadership cash update email. |
| Default Prompt | Use $daily-cash-update to pull the current collections inputs, calculate the Go Get number, and draft the leadership cash update email. |

---

## Purpose

Use this skill when the request is to build the daily leadership cash update from Salesforce aging, the SharePoint AR Tracker, promises-to-pay data, and weekday-specific checks-in-transit context.

---

## Request Shapes

Use this skill for requests like:
- "Build today's cash update and draft the leadership email."
- "Pull the latest collections forecast inputs and calculate the Go Get number."
- "Generate the daily cash update with the right weekday formula and recipient list."
- "Help me with the Friday pulse deck."

---

## Required Tooling

| Source | Purpose |
|--------|---------|
| Advantive Salesforce | Total overdue balance for accounts 60+ days past due |
| Microsoft SharePoint | Collected cash, weekly target, and top 3 aged accounts from the AR Tracker |
| Power BI | Promises to pay (when available — if not, flag as missing input, do not invent) |
| Cash App Updates Teams chat | Tuesday checks in transit — Josh Snow is no longer at Advantive, source unconfirmed. Rep must identify current source before including. |

---

## Workflow

### Step 1 — Determine Weekday

Determine the current weekday before calculating any output. Weekday drives the formula and the checks-in-transit rule.

### Step 2 — Pull Salesforce Overdue Balance

Pull the total overdue balance for accounts where `Days_Overdue__c >= 60`.

- **Preferred:** Aggregate total overdue balance for the 60+ DPD set
- **Fallback:** Retrieve row-level balances and sum them only if aggregate retrieval is unavailable

### Step 3 — Pull SharePoint AR Tracker

Pull these values from the SharePoint AR Tracker:
- Collected cash for the current week
- Weekly target
- Top 3 aged accounts

### Step 4 — Pull Promises to Pay

Pull promises to pay from Power BI when available. If the source is unavailable, inaccessible, or not configured, label that gap clearly — do not invent a number.

### Step 5 — Apply Checks in Transit Rules

| Weekday | Rule |
|---------|------|
| Tuesday | Include the Checks in Transit line — Josh Snow is no longer at Advantive, source unconfirmed. Mark as missing Tuesday input and flag that rep must confirm current source before including. |
| Wednesday / Thursday | Remove the Checks in Transit line (checks have cleared the bank) |
| Friday / Monday | Do not include a Checks in Transit line |

### Step 6 — Calculate Go Get

Apply the weekday-aware formula:

- **Tuesday:** `Weekly Target - Collected Cash - Promises to Pay - Checks in Transit`
- **All other weekdays:** `Weekly Target - Collected Cash - Promises to Pay`

### Step 7 — Friday Pulse Deck Rule

Treat the Friday pulse deck as a **separate** Friday deliverable from the standard daily cash update email. If the user asks about or asks to generate it:
- Acknowledge it exists as a separate Friday send for the CFO and select ELT members
- State that the detailed pulse-deck format is not yet captured in the current materials
- Ask the user to provide the format or template before attempting to build it

Also: **omit the Path to Weekly Target section entirely on Fridays.**

### Step 8 — Draft the Leadership Email

Use this exact subject pattern:
> `DELIVERY | Collections Forecast as of <current date>`

**Recipient list (use unless the user explicitly overrides):**
- **To:** Ryan Asche, Phil Burroughs
- **CC:** Joy Jones, Justin Wixom, Jordan Duke

**Formatting rules:**
- Always spell `Ryan Asche` exactly — never `Ryan Ashe`
- Use no salutation by default — do not open with `Collections,` or any greeting addressed to the collections team
- Open directly with the first content line
- If any required value is missing, still draft the email with clearly labeled placeholders — do not invent numbers
- For the top 3 aged accounts, include a concise status line using only grounded facts from retrieved sources
- When a remaining balance amount is available, include the specific dollar amount — do not replace with generic wording such as `remaining balance`

---

## Output Contract

Always return these sections in this order:

### 1. Retrieved Inputs

List:
- 60+ DPD overdue balance total
- Collected cash
- Weekly target
- Promises to pay
- Checks in transit (when applicable under weekday rules)
- Top 3 aged accounts
- Any missing inputs

### 2. Calculations

Include:
- Weekday used
- Exact Go Get formula applied
- Go Get result
- Whether the Path to Weekly Target section is included or omitted
- Whether the Checks in Transit line is included, removed, or not applicable for that weekday

### 3. Leadership Email Draft

Return a complete draft with:
- Subject line
- To line
- CC line
- Concise body
- Forecast numbers that were successfully retrieved
- Placeholders or callouts for anything still missing
- No salutation by default
- `Ryan Asche` spelled correctly everywhere it appears
- Specific remaining-balance dollar amounts whenever available from retrieved inputs

If the user asked for the Friday pulse deck instead of the daily cash update email, do not improvise the deck. State that it is a separate Friday deliverable, that its detailed format is not yet captured in the current materials, and ask the user to provide the format or template.

---

## Quality Bar

- Do not invent totals, tracker values, promises to pay, or checks in transit.
- Use the Tuesday formula only on Tuesday.
- Do not include a Checks in Transit line on Monday or Friday.
- On Wednesday and Thursday, remove the Checks in Transit line once checks have cleared the bank.
- Omit the Path to Weekly Target section entirely on Friday — not just its numeric values.
- If Power BI data is unavailable, say so explicitly and continue with a clearly labeled draft.
- Keep the leadership email concise and operational.
- Do not address the email to the collections team.
- Do not replace known dollar amounts with generic balance wording.
- Do not confuse the Friday pulse deck with the standard daily cash update email.
