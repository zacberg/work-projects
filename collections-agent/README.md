# Collections Agent

A ChatGPT Custom GPT built for Advantive's AR Collections Department. The agent automates and assists with 11 recurring collections workflows, operating in shadow mode (draft and analyze only — no system writes).

This repo is the version-controlled source of truth for the GPT's configuration so it can be rebuilt, audited, or handed off without depending on one person's ChatGPT account.

> The `master` branch contains the legacy Claude Code version of this agent, kept for reference. The current production GPT is on this branch.

**Status: Live.** The agent is deployed as a ChatGPT Custom GPT and is in active use by Jordan Duke and the collections team.

---

## Architecture

| Component | Detail |
|-----------|--------|
| Agent platform | ChatGPT Custom GPT |
| Capabilities enabled | Web Search, Code Interpreter |
| Data access | SharePoint connector (live strategic-account list, SOPs); NetSuite and Salesforce via user-pasted context or uploaded files |
| Integrations | None — shadow mode only; no system writes |

---

## What it does

The agent handles 11 workflows for the collections team (Jordan Duke and authorized collections leaders, analysts, and operators):

1. Third-party placement tracker
2. Support hold audit
3. Daily cash update generator
4. Collections email drafting assistant
5. Portal submission tracker
6. Write-off and decommission workflow
7. Settlement and legal exclusion check
8. Payment plan risk review
9. SOP cleanup assistant
10. Customer status summary tool
11. Demand and termination letter automation

The agent drafts, analyzes, summarizes, reconciles, and flags issues. It does not send emails, close opportunities, modify Salesforce or NetSuite records, place customers with agencies, or perform any system writes. Any step requiring a system change is performed by a collections leader, Jordan, Billing Ops, Business Systems, Finance Operations, or a Salesforce admin.

---

## Data sources (priority order)

1. **NetSuite** — invoice balances, days past due, aging, open amounts, payment history, invoice numbers, due dates, demand-letter invoice detail, operational hold status
2. **Salesforce** — CRM context only: support holds, legal notes, CSM assignments, opportunities, case context
3. **Microsoft Outlook Email** — prior communications and draft context
4. **Attached uploaded files** — approved SOPs, templates, and reference material (System Audit Addendum, email template examples)
5. **Microsoft SharePoint** — live tracker content, current SOP checks, and the live strategic-account reference file

When NetSuite and any other source conflict on a balance, invoice figure, DPD value, aging figure, or due-date detail, NetSuite always takes precedence.

The agent checks the live SharePoint strategic-account list before drafting any customer-facing outbound contact (collections email, demand letter, termination letter). Accounts on that list are flagged as strategic restrictions and routed to internal review rather than auto-contacted.

---

## Repo structure

| Path | Purpose |
|------|---------|
| `instructions.md` | Full GPT system prompt — paste into the ChatGPT Configure tab |
| `skills/` | One `.md` file per workflow skill — the agent uses these as workflow contracts |
| `knowledge-base/` | SOPs, templates, and reference files uploaded to the GPT's Knowledge |
| `Collections Agent Documentation` | Extended documentation folder |

---

## How to rebuild the GPT

1. ChatGPT -> **My GPTs** -> **Create** (or Edit) -> **Configure** tab
2. Paste `instructions.md` into the Instructions field
3. Upload all files in `knowledge-base/` to **Knowledge**
4. Upload all files in `skills/` to **Knowledge** as well
5. Enable **Web search** and **Code Interpreter** per the original configuration

---

## Skills

| Skill file | Workflow |
|------------|---------|
| `daily-cash-update.md` | Generates the daily cash update email for Jordan |
| `demand-and-termination-letters.md` | Drafts demand / termination letters for delinquent accounts |
| `payment-plan-risk-review.md` | Reviews active payment plans for broken-promise risk |
| `portal-submission-tracker.md` | Tracks and reconciles portal billing submissions |
| `settlement-and-legal-exclusion-check.md` | Checks accounts against legal exclusion and settlement lists |
| `support-hold-audit.md` | Audits support holds — identifies holds to lift, extend, or escalate |
| `third-party-placement-tracker.md` | Tracks accounts sent to third-party collections agencies |
| `write-off-candidates.md` | Surfaces and packages write-off and decommission candidates |

---

_Last updated: 2026-07-20_
