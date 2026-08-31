# Collections Agent — Technical Documentation

**Status:** Live  
**Platform:** ChatGPT Custom GPT (GPT-4o, ChatGPT Enterprise)  
**Last updated:** 2026-07-27  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Sources and Integrations](#data-sources-and-integrations)
4. [Workflows (11 Features)](#workflows-11-features)
5. [How the Agent Works — Full Flow](#how-the-agent-works--full-flow)
6. [Repo Structure](#repo-structure)
7. [Deploying and Rebuilding the GPT](#deploying-and-rebuilding-the-gpt)
8. [Updating the Agent](#updating-the-agent)
9. [Maintenance and Connector Health](#maintenance-and-connector-health)
10. [Known Issues and Limitations](#known-issues-and-limitations)
11. [Key Contacts](#key-contacts)

---

## Overview

The Collections Agent is a ChatGPT Custom GPT deployed on ChatGPT Enterprise for Advantive's AR Collections Department. It assists Jordan Duke and the collections team with 11 recurring workflows — drafting emails, analyzing accounts, generating reports, and recommending actions.

The agent operates in **shadow mode**: it drafts, analyzes, summarizes, and flags issues, but it never sends emails, modifies records, closes opportunities, places accounts with agencies, or makes any system writes. Every step that requires a system change is performed manually by a collections leader, Jordan Duke, Billing Ops, Business Systems, Finance Operations, or a Salesforce admin.

---

## Architecture

| Component | Detail |
|-----------|--------|
| Platform | ChatGPT Custom GPT |
| Model | GPT-4o (ChatGPT Enterprise) |
| Capabilities enabled | Web Search, Code Interpreter |
| Operating mode | Shadow mode — read-only, no system writes |
| Live connectors | NetSuite (AR data), Salesforce (CRM), Microsoft SharePoint, Microsoft Outlook |
| YayPay | Not connected — referenced as process baseline only |
| Knowledge files | SOPs, email templates, skills (workflow contracts), assignment docs |

The agent is configured via two main inputs in the ChatGPT GPT editor:

- **Instructions field** — the full system prompt (`instructions.md`). This contains all operating rules, feature-specific behavior, data source priority, safety constraints, and SOQL/SuiteQL query logic.
- **Knowledge** — uploaded files including skills (workflow contracts) and the knowledge-base folder (SOPs, email templates, process documents, assignment docs).

---

## Data Sources and Integrations

Data sources are used in the following priority order. When sources conflict on an AR fact (balance, DPD, invoice amount, due date), NetSuite always takes precedence.

### 1. NetSuite (Primary — AR Data)

- **What it provides:** Invoice balances, days past due, aging buckets, open amounts, customer payment history, invoice numbers, due dates, demand-letter invoice detail, and operational hold status.
- **Access type:** Live connector — read-only. The agent may query NetSuite but must not create, edit, delete, or change any record.
- **Key rule — Clean-USD scope:** All aggregate AR queries must filter to `BUILTIN.DF(currency)='USD' AND NVL(exchangerate,1)=1` to exclude roughly 63 international-brand USD invoices carrying corrupt exchange rates (1.4–3.7x). Without this filter, the headline 60+ total roughly doubles (~$3.4M–$4.0M vs. the correct ~$1.8M–$2.1M range).
- **Key rule — Strict thresholds:** The dashboard uses strict greater-than thresholds for balance calculations (`daysoverduesearch > 60`) but inclusive thresholds for population filters (`max_dpd >= 60`). This means accounts at exactly the 60-day boundary are counted in the population but contribute $0 to the balance — this is correct and expected.
- **Permissions note:** The NetSuite customer record object returns `INSUFFICIENT_PERMISSION`. Collections rep data must be read from the Transaction field `custbody_scg_collection_rep` at the invoice level, not from the customer record.

### 2. Salesforce (Secondary — CRM Context)

- **What it provides:** Support holds, legal notes, CSM assignments, opportunities, case context.
- **Access type:** Live connector — read-only. All Salesforce writes (hold changes, placement flags, opportunity closures) are manual.
- **Default query limit:** `LIMIT 500` unless the user explicitly requests a larger pull.
- **Key fields used across workflows:**

  | Field | Use |
  |-------|-----|
  | `Total_Overdue_Balance__c` | Per-account overdue balance (use for write-off, email drafting, placement) |
  | `Days_Overdue__c` | Per-account DPD |
  | `Support_Hold__c` | Hold state (boolean) |
  | `Account_Litigation_Hold__c` | Legal block — auto-disqualifies from placement and demand letters |
  | `Bankruptcy_Hold__c` | Legal block — auto-disqualifies from placement and demand letters |
  | `Legal_Notes__c` | Keyword scan triggers REVIEW FLAG |
  | `X3rd_Party_Collections__c` | Third-party placement flag |
  | `Strategic_Account__c` / `Strategic_Account_Child__c` | Strategic restriction flags |
  | `CSM_Name_Text__c` | CSM/AM assignment |
  | `Collections_Rep__c` | Collections rep (incomplete — use NetSuite Transaction level for rep-based breakdowns) |
  | `SCG_Active_ARR__c` | Annual recurring revenue — used for hold qualification and ARR-percentage calculations |

- **Important limitation:** `Total_Overdue_Balance__c` does not apply the clean-USD guardrail and uses different thresholds from the dashboard. Use it only for per-account context in CRM workflows — never to compute or verify portfolio-level totals that need to reconcile with the dashboard.

### 3. Microsoft Outlook Email

- **What it provides:** Prior communications and draft context for account emails.
- **Access type:** Live connector — read-only.

### 4. Attached Uploaded Files (Knowledge)

- **What it provides:** Approved SOPs, email templates, and reference material uploaded to the GPT's Knowledge.
- **Includes:** All files in `knowledge-base/` and all skill files in `skills/`.

### 5. Microsoft SharePoint

- **What it provides:** Live tracker content, current SOP checks, and the live strategic-account reference file.
- **Strategic account list:** `https://advantiveadmin.sharepoint.com/sites/OrdertoCash/Shared Documents/Finance Operations/01 - Accounts Receivable/07 - TOP Accounts/Strategic customer list 5.20.26.xlsx?web=1`
- **Rule:** Before the agent drafts any customer-facing outbound contact (collections email, demand letter, termination letter), it checks this live file. Accounts on the list are flagged as strategic restrictions and routed to internal review — never auto-contacted. If a static uploaded copy conflicts with the live SharePoint file, the live file always wins.

### YayPay (Not Connected)

YayPay is Advantive's operational baseline for dunning templates, Promise-to-Pay workflows, broken-promise handling, and placement notices. The agent treats YayPay processes as the default baseline when relevant, but it has no live YayPay access. Promises-to-pay figures (Feature 3 cash update) are a known manual gap — the agent will flag them as missing rather than invent numbers.

---

## Workflows (11 Features)

Each numbered workflow maps to a skill file in `skills/`. The instructions file references each skill as the authoritative workflow contract.

| Feature | Workflow | Skill file |
|---------|----------|------------|
| 1 | Third-party placement tracker | `third-party-placement-tracker.md` |
| 2 | Support hold audit | `support-hold-audit.md` |
| 3 | Daily cash update generator | `daily-cash-update.md` |
| 4 | Collections email drafting assistant | (rules in `instructions.md`) |
| 5 | Portal submission tracker | `portal-submission-tracker.md` |
| 6 | Write-off and decommission workflow | `write-off-candidates.md` |
| 7 | Settlement / legal exclusion check | `settlement-and-legal-exclusion-check.md` |
| 8 | Payment plan risk review | `payment-plan-risk-review.md` |
| 9 | SOP cleanup assistant | (rules in `instructions.md`) |
| 10 | Customer status summary tool | (rules in `instructions.md`) |
| 11 | Demand and termination letter automation | `demand-and-termination-letters.md` |

**Feature 7 (legal check) gates Features 1 and 11** — the legal/exclusion check runs first for any placement or demand-letter workflow. Accounts with `Account_Litigation_Hold__c = true` or `Bankruptcy_Hold__c = true` are BLOCKED; accounts with legal keywords in `Legal_Notes__c` surface as REVIEW FLAG for human review.

---

## How the Agent Works — Full Flow

A typical agent interaction follows this sequence:

1. **User submits a request** in ChatGPT (e.g., "Run the placement tracker" or "Draft a collections email for Acme Corp").

2. **The agent identifies the workflow** by matching the request to one of the 11 features. If the request matches a skill, the agent loads that skill's workflow contract for detailed steps.

3. **Retrieval-first:** The agent attempts to retrieve all needed data from connected systems before asking the user to provide anything manually:
   - NetSuite for AR data (balances, DPD, invoice details)
   - Salesforce for CRM context (holds, legal notes, CSM, opportunities, cases)
   - SharePoint for live tracker content and strategic account list
   - Outlook for prior communications when relevant

4. **Legal / strategic screening runs first** for any workflow that could result in customer-facing outbound contact. Accounts that are BLOCKED (litigation hold, bankruptcy hold) stop here. Accounts with a REVIEW FLAG are surfaced for human review before proceeding. Strategic account list is checked before any outbound draft is produced.

5. **The agent drafts the output** — a report, email draft, letter, or analysis — using grounded data from the retrieved sources. It does not invent invoice numbers, payment dates, contact names, or system state.

6. **Output is returned to the user** for review. The user (or a collections leader) makes any decisions and executes any system changes manually. The agent never writes back to any system.

### Shadow mode — what this means in practice

Every output from the agent is a draft, recommendation, or analysis only:
- Emails are drafts — never sent by the agent
- Placement lists are recommendations — the actual TAA placement flag (`X3rd_Party_Collections__c`) is set manually by Jordan Duke or Business Systems
- Write-off reports are candidate packages — the write-off is approved and processed manually by Finance Ops
- Support hold recommendations are flagged for manual action — holds are applied or released in Salesforce by a Salesforce admin or authorized user
- Legal checks are screenings — the agent surfaces flags and routes them for human decision

---

## Repo Structure

| Path | Purpose |
|------|---------|
| `instructions.md` | Full GPT system prompt — paste into the ChatGPT Configure > Instructions field |
| `skills/` | One `.md` file per workflow skill — uploaded to GPT Knowledge alongside knowledge-base files |
| `knowledge-base/` | SOPs, email templates, process documents, assignment docs — uploaded to GPT Knowledge |
| `agent-scripts/` | Python reference scripts (`ar_agent_config.py`, `ar_agent_queries.py`, `ar_agent_templates.py`) — reference only, not uploaded to GPT |
| `Collections Agent Documentation/` | Extended documentation folder (Word docs) |

The `agent-scripts/` folder contains Python files that document confirmed field names, SOQL query patterns, thresholds, and business rules. These are version-controlled reference material — they are not executed by the GPT. Some values in those files may be stale (e.g., former employee names in distribution lists, old agency name "Altus" superseded by "TAA") — the `instructions.md` and skill files are authoritative.

---

## Deploying and Rebuilding the GPT

To rebuild the GPT from scratch (e.g., after a ChatGPT account change or GPT deletion):

1. Go to **ChatGPT > My GPTs > Create** (or Edit an existing GPT).
2. Open the **Configure** tab.
3. Paste the full contents of `instructions.md` into the **Instructions** field.
4. Upload all files from `knowledge-base/` to **Knowledge**.
5. Upload all files from `skills/` to **Knowledge** as well.
6. Enable **Web search** and **Code Interpreter** under Capabilities.
7. Verify that the live connectors (NetSuite, Salesforce, SharePoint, Outlook) are connected and authenticated.
8. Test with a representative request for each feature before handing back to users.

---

## Updating the Agent

### Updating the system prompt (instructions.md)

1. Edit `instructions.md` in the repo.
2. Commit the change.
3. In ChatGPT, open the GPT editor > Configure > Instructions field.
4. Replace the current contents with the updated `instructions.md`.
5. Save the GPT.

### Updating knowledge files or skill files

1. Edit the relevant file in `knowledge-base/` or `skills/`.
2. Commit the change.
3. In ChatGPT, open the GPT editor > Knowledge section.
4. Delete the old version of the file.
5. Upload the updated file.
6. Save the GPT.

### Adding a new skill

1. Create a new `.md` file in `skills/` following the format of existing skill files.
2. Add a reference to it in `instructions.md` under the Skill Directory section and the corresponding feature section.
3. Upload the skill file to GPT Knowledge.
4. Update `instructions.md` in the GPT editor.

### Updating the strategic account list

The strategic account list is read live from SharePoint — no GPT update is needed when the list changes. The agent always fetches the live version.

---

## Maintenance and Connector Health

### Connector health checks

If a connector is not returning data, the agent will surface what is missing rather than fabricating values. Signs of a broken connector:

- The agent says it cannot access NetSuite / Salesforce / SharePoint and asks the user to paste data manually
- AR balance figures are missing or zero when accounts should have balances
- The strategic account check cannot complete

To restore a connector: re-authenticate in the ChatGPT GPT editor under the connector settings. Credential rotation (Salesforce OAuth, NetSuite tokens, M365 OAuth) may be required periodically.

### Credential rotation

| Connector | Auth type | Who manages it |
|-----------|-----------|----------------|
| Salesforce | OAuth (ChatGPT connector) | Business Systems / ChatGPT Enterprise admin |
| NetSuite | OAuth or token (ChatGPT connector) | Business Systems / ChatGPT Enterprise admin |
| SharePoint (M365) | OAuth (ChatGPT connector) | IT / ChatGPT Enterprise admin |
| Outlook (M365) | OAuth (ChatGPT connector) | IT / ChatGPT Enterprise admin |

If a connector fails or needs re-credentialing, contact Business Systems (Jaime) or the ChatGPT Enterprise admin.

### Keeping knowledge files current

The SOPs and email templates in `knowledge-base/` should be reviewed when process changes are made. Stale knowledge files will produce drafts based on outdated process. Update the knowledge file in the repo and re-upload to GPT Knowledge.

### Checking for stale configuration

The `agent-scripts/ar_agent_config.py` file documents confirmed thresholds and business rules. Review it periodically against the instructions to catch drift. Known stale values as of the last update:
- `PLACEMENT_AGENCY = "Altus"` — superseded by "TAA" in `instructions.md`
- `CASH_UPDATE_TO` and `CASH_UPDATE_CC` in the config include former employees — `instructions.md` is authoritative for the current recipient list

---

## Known Issues and Limitations

### YayPay not connected
YayPay is not a connected data source. Promises-to-pay figures (used in Feature 3 cash update Go Get calculation) cannot be retrieved automatically. The agent will flag this as a missing input and output a placeholder. The user must provide PTP figures manually until YayPay is connected.

Outreach-attempt counts (used for placement eligibility in Feature 1) are also a manual gap for the same reason.

### Tuesday checks in transit — source unconfirmed
The cash update (Feature 3) includes a checks-in-transit line on Tuesdays. The historical source was Josh Snow, who is no longer at Advantive. The agent will flag this as an unconfirmed source and prompt the user to identify the current source before including the figure.

### NetSuite customer record permission block
The NetSuite customer record object returns `INSUFFICIENT_PERMISSION`. Collections rep data must be read from the Transaction field `custbody_scg_collection_rep` at the invoice level. The agent handles this correctly, but it means the CSM/AM assignment must always be retrieved from Salesforce, not NetSuite.

### NetSuite–Salesforce customer ID crosswalk unconfirmed
The mapping between `Harmony_Customer_ID__c` (Salesforce) and the NetSuite entity ID has not been confirmed. The agent cannot reliably cross-reference between systems using this field. Account matching is done by name.

### Salesforce `Total_Overdue_Balance__c` does not match the dashboard
This field is pre-computed and does not apply the clean-USD guardrail or strict threshold logic used by the AR Collections Dashboard. Aggregate portfolio totals calculated using this field will differ from dashboard figures and cannot be reconciled to them. Use the SuiteQL clean-USD query for any figure that needs to match the dashboard.

### `SCG_Active_ARR__c` null or zero
When this field is null or zero on an account, the agent skips ARR-percentage calculations for that account and flags it as a data-quality review item. This affects Feature 2 (support hold audit) hold qualification.

### 2000-record Salesforce limit
ChatGPT's Salesforce connector enforces a 2000-record limit per query. For portfolio-wide scans with large result sets, the query may not return every eligible account. The agent uses `LIMIT 500` as a default safety floor.

### YayPay dunning coordination — manual
The agent runs alongside YayPay's automated dunning sequences. There is no live integration, so the agent cannot see what YayPay has already sent to a customer. The user should check YayPay's outreach history before directing the agent to draft a collections email, to avoid duplicating an automated sequence.

---

## Key Contacts

| Name | Role | Email |
|------|------|-------|
| Jordan Duke | AR Sr Manager — feature owner, primary user | jordan.duke@advantive.com |
| Justin Wixom | Sr Director Finance Operations | justin.wixom@advantive.com |
| Joy Jones | Controller | joy.jones@advantive.com |
| Ryan Asche | CFO | ryan.asche@advantive.com |
| Phil Burroughs | — | phil.burroughs@advantive.com |
| Tiffany Johnson | Billing Ops Manager | tiffany.johnson@advantive.com |
| Gaby Vitoria | Settlement contact | gaby.vitoria@advantive.com |

For connector issues or GPT access problems, contact Business Systems (Jaime) or the ChatGPT Enterprise admin.

---

_Source of truth for GPT configuration: `instructions.md` and `skills/` in this repo. The `agent-scripts/` folder is reference material only._
