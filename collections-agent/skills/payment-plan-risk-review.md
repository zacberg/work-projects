# Skill — Payment Plan Risk Review

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `payment-plan-risk-review` |
| Display Name | Payment Plan Risk Review |
| Short Description | Review payment plan risk and approval needs. |
| Trigger Description | Use when the user asks to review payment plan risk from Salesforce account context, flag long-plan, annual-upfront renewal, or broken-prior-plan risk, and draft an approval or denial recommendation for Jordan Duke. |
| Default Prompt | Use $payment-plan-risk-review to review payment plan risk, flag approval concerns, and draft a recommendation for Jordan Duke. |

---

## Purpose

Use this skill when the request is to evaluate whether a delinquent account is a good payment-plan candidate, summarize the main risk factors, and draft an approval or denial recommendation for Jordan Duke.

---

## Request Shapes

Use this skill for requests like:
- "Review this account for payment plan risk and draft a recommendation for Jordan."
- "Flag payment plan risks, including long plan risk and broken prior plan risk."
- "Evaluate whether this delinquent annual-billing account should get a payment plan."

---

## Required Tooling

**Advantive Salesforce** — primary source for overdue balance, days past due, ARR, hold state, legal notes, CSM, and any payment-plan history or annual-billing evidence available in Salesforce.

---

## Workflow

### Step 1 — Resolve Account

Accept the target account or account list and resolve each one to the smallest reliable Salesforce record set.

### Step 2 — Retrieve Account Context

Retrieve core account context:
- `Name`
- `Total_Overdue_Balance__c`
- `Open_Balance__c`
- `Days_Overdue__c`
- `SCG_Active_ARR__c`
- `Support_Hold__c`
- `Finance_Hold_Status__c` (when available)
- `Legal_Notes__c`
- `CSM_Name_Text__c`

Also retrieve any available Salesforce evidence for:
- Current proposed plan length in days
- Installment count
- Prior payment plan failure or broken commitment history
- Annual billing or annual-upfront renewal structure

If plan length, installment count, prior-plan history, or annual-billing evidence is not available in Salesforce, label the missing element as a data gap instead of inferring it.

### Step 3 — Apply Risk Flags

**Long Plan Risk** — flag when either condition is true:
- The plan is over 90 days
- The plan has more than 3 installments

**Annual Upfront Renewal Risk** — flag when both are true:
- The account is delinquent
- Available Salesforce evidence shows annual billing or annual-upfront renewal structure

**Broken Prior Plan Risk** — flag when prior payment plan failure, broken commitments, or failed prior arrangements are evident in the retrieved Salesforce data.

Treat legal notes and hold state as contextual risk signals. Surface them in the recommendation even when they are not the primary reason for approval or denial.

### Step 4 — Draft Recommendation

Draft an approval or denial recommendation for Jordan Duke that includes:
- Recommendation outcome
- Main rationale
- Any conditions that should apply if approved
- Any blocking concerns or missing information that should be reviewed before approval

Explicitly remind the reader that **every payment plan requires Jordan Duke's approval** before moving forward.

Do not present any payment plan as approved, active, or finalized unless the user confirms that approval already occurred.

---

## Output Contract

Always return these sections in this order:

### 1. Account Context
For each account include:
- Account name
- Overdue balance
- Open balance when available
- Days past due
- ARR when available
- Hold state
- CSM
- Any relevant legal-note context

### 2. Risk Flags
For each account include:
- Long Plan Risk status and evidence
- Annual Upfront Renewal Risk status and evidence
- Broken Prior Plan Risk status and evidence
- Any additional contextual concerns or data gaps

### 3. Recommendation Draft for Jordan Duke
Return a concise internal approval-or-denial recommendation that includes:
- Recommendation outcome
- Rationale
- Approval conditions if applicable
- Unresolved issues or missing inputs
- Explicit note that Jordan Duke must approve before any payment plan moves forward

---

## Quality Bar

- Do not invent plan length, installment count, billing cadence, or prior-plan history.
- If annual billing cannot be verified from retrieved Salesforce evidence, say so explicitly instead of assuming risk.
- Keep legal-note usage factual — do not convert note text into unsupported legal conclusions.
- If no risk is found for a category, say so explicitly instead of omitting it.
- Keep the recommendation concise, operational, and ready for Jordan Duke's review.
