# Case Resolution Summary Generator — Technical Documentation

**Tool:** ChatGPT Enterprise Custom GPT  
**Repo:** `Advantive-Business-Systems/case-agents` (or local: `C:\Users\ZachBergman\_docs-work\case-resolution-agent-zb\`)  
**Last updated:** 2026-07-27

---

## Table of Contents

1. [How the Agent Works](#1-how-the-agent-works)
2. [Architecture](#2-architecture)
3. [Configuration and Deployment](#3-configuration-and-deployment)
4. [Maintenance and Support](#4-maintenance-and-support)
5. [Field Reference](#5-field-reference)
6. [Known Issues and Constraints](#6-known-issues-and-constraints)

---

## 1. How the Agent Works

### Full Request Flow

**Step 1 — Tech provides a case number**

The support tech opens the GPT in ChatGPT Enterprise and types a case number (e.g., `00786393`). The GPT also accepts a Salesforce URL or a customer/account name; in those cases it normalizes the input before proceeding.

**Step 2 — GPT calls the n8n webhook (GET)**

The GPT fires the `readCaseDetail` action:

```
GET https://advantive.app.n8n.cloud/webhook/case-resolution/summary?caseNumber=00786393
```

n8n receives the request, runs two SOQL queries against Salesforce Service Cloud:
1. Fetch the `Case` record by `CaseNumber` — returns all case fields plus the `Account` and `Contact` lookups.
2. Fetch child `EmailMessages` for that case `Id` — this is the email thread/feed.

A sanitizer Code node inside n8n allowlists which fields are returned to the GPT (see [Section 5](#5-field-reference) for the full list). The sanitized JSON is returned to ChatGPT.

**Step 3 — GPT displays case header**

Before drafting anything, the GPT shows the tech a formatted case header for context. This header is never saved to Salesforce. Fields shown:

- Generated date
- Case number (Account Name)
- Priority
- Business Unit
- Support Product
- ADO Work Item ID
- Dev Issue #
- Opened (CreatedDate)
- Last activity (Last_Status_Change_Date__c)
- Resolved/closed (Resolution_Delivered_Date__c / ClosedDate)
- Days open

Any unavailable field is shown as `N/A` — the label is always present.

**Step 4 — GPT drafts the four-section resolution**

The GPT analyzes the case fields and email feed and drafts a resolution in the team's standard format (see [USER_GUIDE.md](USER_GUIDE.md) for what each section means). The draft is grounded in the retrieved data only — the GPT does not invent steps, dates, or outcomes.

**Step 5 — Tech reviews and confirms**

The tech reads the draft. The GPT ends each draft with the exact prompt:

> `Ready to save this to Salesforce — want me to push it?`

The GPT will not save anything automatically. The tech must explicitly confirm.

**Step 6 — GPT calls the n8n webhook (POST)**

After confirmation, the GPT fires the `pushResolution` action:

```
POST https://advantive.app.n8n.cloud/webhook/case-resolution/summary
Content-Type: application/json

{
  "caseNumber": "00786393",
  "summary": "<four-section block only>"
}
```

Only the four-section resolution block is sent — the case header, tech-only section, prior-case references, and confidence notes are never included in the POST body.

n8n receives the POST, looks up the Salesforce Case `Id` by `CaseNumber`, and calls the Salesforce REST API to update `Resolution_Summary__c` on that record.

**Step 7 — Confirmation or fallback**

- HTTP 200: GPT says `Resolution summary saved.`
- Any failure: GPT says `The push didn't go through — please paste it into the Resolution tab manually.` and displays the block for manual copy-paste.

---

## 2. Architecture

```
Support Tech (ChatGPT Enterprise)
        |
        |  [1] Type case number
        v
+---------------------------+
|  Custom GPT               |
|  Model: GPT-4o            |
|  Action: OpenAPI schema   |
+---------------------------+
        |                        |
        |  GET ?caseNumber=...    |  POST {caseNumber, summary}
        v                        v
+----------------------------------------------+
|  n8n Cloud (advantive.app.n8n.cloud)         |
|                                              |
|  Webhook trigger (GET)                       |
|    → SOQL: fetch Case by CaseNumber          |
|    → SOQL: fetch EmailMessages by Case Id    |
|    → Sanitizer Code node (field allowlist)   |
|    → Return JSON to GPT                      |
|                                              |
|  Webhook trigger (POST)                      |
|    → SOQL: lookup Case Id by CaseNumber      |
|    → Salesforce update: Resolution_Summary__c|
+----------------------------------------------+
        |                        |
        v                        v
+----------------------------------------------+
|  Salesforce Service Cloud                    |
|  (advantive.my.salesforce.com)               |
|  Read: Case + EmailMessages                  |
|  Write: Resolution_Summary__c               |
+----------------------------------------------+
```

**Why n8n instead of the native ChatGPT connector?**

ChatGPT Enterprise cannot have both a custom OpenAPI Action and a connector App active on the same GPT simultaneously. The native ChatGPT↔Salesforce connector also had org-wide access issues (returns errors even with admin approval). n8n is used as the middleware layer: it handles Salesforce OAuth, runs targeted SOQL, enforces the field allowlist, and provides a stable webhook endpoint that the GPT calls via the OpenAPI Action.

---

## 3. Configuration and Deployment

### 3.1 Repo file map

| File | Purpose |
|------|---------|
| `engineer-tool/instructions.md` | Full GPT system prompt |
| `engineer-tool/openapi-schema.json` | OpenAPI 3.1 schema for the GPT Action |
| `engineer-tool/n8n-case-resolution-workflow.json` | n8n workflow (import into n8n Cloud) |
| `engineer-tool/salesforce-action.md` | Salesforce field reference and SOQL queries |
| `engineer-tool/gpt-logo.png` | GPT profile logo |

### 3.2 Updating the GPT system prompt

1. Edit `engineer-tool/instructions.md` in this repo.
2. Open ChatGPT Enterprise → **My GPTs** → **Case Resolution Summary Generator** → **Edit** → **Configure** tab.
3. Select all text in the **Instructions** field and replace it with the new content.
4. Click **Save**.

The GPT updates immediately on save. Test on a known closed case before announcing changes to the team.

### 3.3 Updating the OpenAPI schema

The schema defines the two webhook endpoints (`readCaseDetail` GET and `pushResolution` POST). Update if the n8n webhook URL changes or if the request/response structure changes.

1. Edit `engineer-tool/openapi-schema.json` in this repo.
2. Open the GPT in Edit mode → **Configure** tab → scroll to **Actions** → click the action name.
3. Replace the schema content with the updated JSON.
4. Click **Save** on the action, then **Save** on the GPT.
5. Test both GET and POST from the GPT action tester before deploying.

### 3.4 Updating the n8n workflow

1. Open `engineer-tool/n8n-case-resolution-workflow.json` in this repo and make changes, or edit the live workflow directly in n8n Cloud (`advantive.app.n8n.cloud`).
2. If editing live: open the workflow → make changes → **Save** → **Activate**. Export and commit the updated JSON to this repo.
3. If importing fresh: n8n Cloud → **Workflows** → **Import from file** → select the JSON → re-attach credentials (Salesforce OAuth and the webhook header secret; see Section 4.1).

The n8n webhook path is `case-resolution/summary`. Do not change this path without also updating `servers.url` and the path in `openapi-schema.json`, and updating the GPT Action.

### 3.5 Rebuilding the GPT from scratch

1. ChatGPT Enterprise → **My GPTs** → **Create** → **Configure** tab.
2. **Name:** `Case Resolution Summary Generator`
3. **Instructions:** paste the full contents of `engineer-tool/instructions.md`.
4. **Actions** → **Create new action** → paste the contents of `engineer-tool/openapi-schema.json`.
5. **Authentication** on the action: set to `API Key`, header name `X-Webhook-Secret` (or whatever header name the n8n workflow checks), value = the secret configured in n8n.
6. Upload `engineer-tool/gpt-logo.png` as the GPT profile image.
7. **Save** and test.

---

## 4. Maintenance and Support

### 4.1 Credential rotation

Two secrets protect the n8n webhook:

| Secret | Location | What it does |
|--------|----------|--------------|
| Webhook header secret | n8n workflow → Webhook node credentials (`Case Resolution Secret`) AND GPT Action authentication settings | Authenticates GPT-to-n8n requests |
| Salesforce OAuth token | n8n workflow → all Salesforce nodes (`Advantive Salesforce` credential, id `zRAf2lM3nxuEpTk8`) | n8n's auth to read/write Salesforce |

**If the Salesforce OAuth credential expires in n8n:**
- Contact Jaime Rennick (Business Systems). She manages the Salesforce connected-app credentials.
- In n8n: navigate to **Credentials** → **Advantive Salesforce** → re-authorize via OAuth.

**If the webhook header secret needs rotation:**
1. Generate a new secret.
2. Update the `Case Resolution Secret` credential in n8n (Credentials → Case Resolution Secret → update value → Save).
3. Update the GPT Action authentication value to match (ChatGPT → Edit GPT → Configure → Actions → edit action → Authentication → update API key value).

### 4.2 If the n8n webhook stops responding

Symptoms: GPT returns an error when given a case number, or the push confirmation never comes back.

Checklist:
1. **Is the n8n workflow active?** Open n8n Cloud → Workflows → confirm the workflow toggle is **Active** (blue). If it's inactive, click to activate.
2. **Are the credentials valid?** Open the workflow, click any Salesforce node, check the credential selector. If it shows a warning, re-authorize (see Section 4.1).
3. **Test the webhook directly.** Use a REST client (Postman, curl) to hit:
   ```
   GET https://advantive.app.n8n.cloud/webhook/case-resolution/summary?caseNumber=<known case number>
   ```
   with the `X-Webhook-Secret` header set. A 200 with JSON = n8n is healthy. A 404 = webhook path is wrong or workflow is inactive. A 5xx = Salesforce query error.
4. **Check n8n execution logs.** Open the workflow → **Executions** tab → find the failed run → inspect which node errored.
5. If Salesforce credentials are the problem, escalate to Jaime.

### 4.3 Testing a change

Always test on a real closed case (one with a known resolution already written) before using on an active case:

1. Give the GPT a closed case number.
2. Confirm the case header fields are correct (compare to Salesforce directly).
3. Confirm the resolution draft is grounded in the email feed.
4. Do **not** confirm the push on a test case that already has a resolution (it would overwrite it). Either use a dedicated test case or stop at step 3.

To test the POST path safely, use a scratch case or ask Jaime to create one.

---

## 5. Field Reference

### Salesforce fields read (via n8n SOQL)

| Field | Object | Description |
|-------|--------|-------------|
| `Id` | Case | Internal Salesforce record ID (used for write-back lookup) |
| `CaseNumber` | Case | Human-readable case number (e.g., 00786393) |
| `Subject` | Case | Case subject line |
| `Description` | Case | Initial case description |
| `Status` | Case | Current status |
| `IsClosed` | Case | Boolean; used to scope historical case searches |
| `Priority` | Case | Case priority (High / Medium / Low) |
| `Type` | Case | Case type |
| `Reason` | Case | Case reason |
| `Case_Category__c` | Case | Case category (custom) |
| `Case_Sub_Reason__c` | Case | Sub-reason (custom) |
| `Case_Research__c` | Case | Tech research notes (custom) — shown in tech-only section, never saved to Salesforce |
| `Account.Name` | Account | Customer account name |
| `Account.Type` | Account | Account type (customer, partner, etc.) — tech-only section |
| `Contact.Name` | Contact | Primary contact name |
| `CreatedDate` | Case | Date case was opened |
| `Last_Status_Change_Date__c` | Case | Last status change (custom) |
| `Resolution_Delivered_Date__c` | Case | Resolution delivered date (custom) |
| `ClosedDate` | Case | Date case was closed |
| `Business_Unit__c` | Case | Business unit (custom) |
| `Support_Product__c` | Case | Support product (custom); `Support_Product_Text__c` used as fallback |
| `ADO_WorkItem_ID__c` | Case | Azure DevOps work item ID (custom); N/A if null |
| `Issue__c` | Case | Dev issue number (custom); N/A if null |
| `Resolution_Summary__c` | Case | Customer-facing resolution field (custom) — this is the write target |
| `Engineering_Resolution__c` | Case | Engineering resolution notes (custom) — read for context |
| `Engineering_Fixed_in_Version__c` | Case | Version where fix shipped (custom) |

### EmailMessages fields read

| Field | Description |
|-------|-------------|
| `TextBody` | Email body text |
| `Incoming` | Boolean — true if customer email, false if outbound |
| `FromAddress` | Sender email address |
| `MessageDate` | Timestamp of the message |

### n8n sanitizer allowlist

The n8n workflow contains Code nodes that strip all Salesforce fields except those listed above before returning data to the GPT. This prevents internal-only fields and sensitive metadata from reaching the model. If a field needs to be added to the GPT's context, it must be added both to the SOQL query in n8n and to the sanitizer allowlist in the corresponding Code node.

### Salesforce write target

Only one field is ever written: `Resolution_Summary__c` on the `Case` object. The write is triggered only by a confirmed `pushResolution` POST. No other fields, records, or objects are modified.

---

## 6. Known Issues and Constraints

| Issue | Detail |
|-------|--------|
| Salesforce OAuth expiry | The n8n Salesforce credential (`Advantive Salesforce`) may need periodic re-authorization. If the webhook returns errors, check this first. Contact Jaime. |
| `ADO_WorkItem_ID__c` and `Issue__c` null | Many cases do not have these fields set. `N/A` in the header is correct and expected. |
| `Support_Product__c` fallback | If `Support_Product__c` is null, the n8n sanitizer falls back to `Support_Product_Text__c`. If both are null, the header shows `N/A`. |
| 2,000-record limit | ChatGPT Enterprise's native Salesforce connector has a 2,000-record limit on bulk queries. This tool routes around it by using n8n with targeted single-case SOQL, which returns exactly one case at a time. |
| CaseComments typically empty | This org uses `EmailMessages` as the primary case feed. `CaseComments` is queried but usually returns nothing. The GPT uses `EmailMessages` as the feed. |
| n8n workflow must be active | If the workflow is paused or deactivated in n8n Cloud, all GPT calls will fail. Check the workflow toggle. |
| One GPT action or connector, not both | ChatGPT Enterprise does not allow a custom OpenAPI Action and a connector App on the same GPT simultaneously. The n8n webhook replaces the native Salesforce connector for this reason. |
