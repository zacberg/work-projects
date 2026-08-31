# Skill — Support Hold Audit

**Version:** V1.25-test
**Files attached:** 2

---

## Metadata

| Field | Value |
|-------|-------|
| Name | `support-hold-audit` |
| Display Name | support-hold-audit |
| Short Description | Audit support holds and legal-review exceptions. |
| Trigger Description | Use when the user asks to audit Salesforce support holds, find release candidates, identify accounts that should be on hold, surface legal-review accounts, and flag Revenue Entity rollup mismatches for Business Systems review. |
| Default Prompt | Use $support-hold-audit to review support hold release candidates, missing holds, legal-review accounts, and Business Systems escalation cases from Salesforce. |

---

## Purpose

Use this skill when the request is to audit support-hold status from Salesforce, separate release candidates from missing-hold accounts, surface legal-review cases, and call out rollup mismatches between Revenue Entity state and account-level hold state.

---

## Request Shapes

Use this skill for requests like:
- "Run a support hold audit and show me release candidates, missing holds, and legal-review accounts."
- "Review all accounts on hold, 45+ days past due, or with bankruptcy/litigation flags and give me the three reports."
- "Find support hold rollup mismatches and flag what should go to Business Systems."

---

## Required Tooling

**Advantive Salesforce** — source for account-level hold status, overdue balances, legal fields, and any available related Revenue Entity hold context.

---

## Workflow

### Step 1 — Query Salesforce

Query Salesforce for accounts where at least one of these conditions is true:
- `Support_Hold__c = true`
- `Days_Overdue__c >= 45`
- `Bankruptcy_Hold__c = true`
- `Account_Litigation_Hold__c = true`

Retrieve the minimum account-level fields needed to classify results:
- `Id`
- `Name`
- `Support_Hold__c`
- `Total_Overdue_Balance__c`
- `Open_Balance__c`
- `Days_Overdue__c`
- `SCG_Active_ARR__c`
- `Strategic_Account__c`
- `Stop_Hold_Override__c`
- `Bankruptcy_Hold__c`
- `Account_Litigation_Hold__c`
- `Legal_Notes__c`

If Salesforce exposes related Revenue Entity hold records or held-entity rollup context, retrieve the smallest useful related data needed to compare Revenue Entity state with account-level `Support_Hold__c`.

### Step 2 — Build Report 1: On Hold With Zero Overdue Balance

Include accounts where:
- `Support_Hold__c = true`
- `Total_Overdue_Balance__c = 0`

Treat these as release candidates. If Revenue Entity hold state still suggests the account should be held, do not call it a clean release candidate — flag it as a Business Systems escalation case instead.

### Step 3 — Build Report 2: Should Be On Hold But Are Not

Include accounts where **all** of these are true:
- `Support_Hold__c = false`
- `Days_Overdue__c >= 45`
- `SCG_Active_ARR__c` is present and greater than zero
- `Total_Overdue_Balance__c >= 15%` of `SCG_Active_ARR__c`
- `Strategic_Account__c != true`
- `Strategic_Account_Child__c != true`
- `Stop_Hold_Override__c != true`
- `Bankruptcy_Hold__c != true`
- `Account_Litigation_Hold__c != true`

Strategic accounts must be excluded from **all** parts of Report 2, including any broader 45+ DPD review population or additional-candidates list. If a strategic account appears in Report 2, treat it as a filter-order bug rather than expected behavior.

If an account also belongs in Report 3 due to litigation, bankruptcy, or legal-note review risk, put it in Report 3 and note that legal review should happen before recommending hold action.

### Step 4 — Build Report 3: Legal Review Required

Include accounts where one or more of these conditions are true:
- `Bankruptcy_Hold__c = true`
- `Account_Litigation_Hold__c = true`
- `Legal_Notes__c` contains one or more canonical legal keywords

**Legal keyword list:**
`settlement`, `settlement agreement`, `settled`, `walkaway`, `walk away`, `walked away`, `legal hold`, `litigation`, `breach`, `dispute`, `termination notice`, `attorney`, `lawsuit`, `do not contact`, `cease and desist`, `bankruptcy`, `remediation`

For every legal-note keyword hit, quote the exact matching text or the smallest useful excerpt that contains the hit.

### Step 5 — Flag Business Systems Escalation Cases

Flag a Business Systems escalation case whenever Revenue Entity state conflicts with the account-level hold result. Examples:
- Revenue Entity state implies the account should still be on hold, but `Support_Hold__c = false`
- Revenue Entity state implies the account should be released, but `Support_Hold__c = true`
- Revenue Entity rollup counts or related-state evidence do not reconcile to the account-level hold outcome

If Revenue Entity state is not available in the current results, state that rollup-mismatch review could not be fully completed and limit the output to account-level findings.

---

## Output Contract

Always return these sections in this order.

Before the sections, include this line exactly:
> `Note: Salesforce automation for hold management is currently unreliable — it is not consistently lifting holds at $0 balance or applying new ones. This audit supplements that broken automation.`

### 1. Report 1: On Hold With Zero Overdue Balance

For each account include:
- Account name
- Overdue balance
- Open balance when available
- Days past due
- Release recommendation
- Whether a Business Systems escalation is needed

### 2. Report 2: Should Be On Hold But Are Not

For each account include:
- `Account Name | DPD | Unpaid $ | ARR $ | Unpaid % | Rep | Legal Flag`
- The ARR threshold calculation as `Unpaid Balance ÷ ARR = X%`
- The label `recommended for hold — pending Jordan approval`
- A short explanation of why the hold threshold is met

Report 2 is a recommendation list only. Do not use language that implies immediate hold action, auto-action, or direct hold application by the agent.

After Report 2 or alongside its heading, include the required manual approval process for new holds:
1. Rep reviews account history and open cases
2. Rep sends hold recommendation to Jordan Duke
3. Jordan approves or denies
4. Rep applies `Support_Hold__c = true` in Salesforce only if approved
5. Hold release requires $0 open balance confirmation or Jordan override

### 3. Report 3: Legal Review Required

For each account include:
- Account name
- Triggered legal-review reason
- Source field or note evidence
- Exact matching text or excerpt when `Legal_Notes__c` caused the flag
- Short note that legal review is required before hold-action recommendation

### 4. Business Systems Escalation Cases

Include only accounts where Revenue Entity state and account-level hold status do not reconcile. For each one include:
- Account name
- Account-level hold state
- Related Revenue Entity evidence when available
- Concise description of the mismatch
- Recommended Business Systems follow-up

---

## Quality Bar

- Do not invent Revenue Entity details, legal conclusions, or missing balances.
- Do not recommend a clean hold or release action when legal-review conditions clearly require human review first.
- Do not calculate the ARR threshold when `SCG_Active_ARR__c` is null or zero — flag that account as a data gap and omit it from Report 2 threshold qualification.
- Do not include strategic accounts anywhere in Report 2 output, broader review populations, or additional-candidate lists.
- If no accounts qualify for a report, say so explicitly instead of omitting the section.
- Keep Business Systems escalations narrow and evidence-based.
