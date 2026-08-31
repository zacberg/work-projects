# Case Agents — Support Case Tooling

This repository contains ChatGPT Custom GPT configurations for the Advantive support organization. The primary tool (Tool 1, live) accepts a case number, Salesforce URL, or customer name from a support technician; retrieves the full case record and email thread from Salesforce via an n8n middleware layer; optionally searches closed cases for a prior fix to the same product issue; drafts a four-section resolution summary in the team's standard format; and — after technician confirmation — writes the approved resolution back to the Salesforce Resolution tab. Two additional tools (case sentiment analysis and historical resolution finder) are in the planning stage.

Configuration is version-controlled here so any tool can be rebuilt, audited, or handed off without depending on one person's ChatGPT account.

**Full requirements (2026-06-25 meeting): see `REQUIREMENTS.md`.**

**Stakeholders:** Jaime Rennick, Michelle Johnson (vision and sign-off); Rashtin (Resolution GPT co-builder); Mark (historical resolution finder, scope to be defined)

---

## Tool 1 — Resolution Summary GPT (Live)

**What it does:** A tech gives the GPT a case number, Salesforce URL, or customer name. The GPT pulls the full case record and email thread from Salesforce, optionally searches closed cases for a known fix for the same product, drafts a resolution in the team's four-section template, and — after the tech confirms — saves the approved text back to the Salesforce Resolution tab.

**Architecture:**
```
ChatGPT GPT
  ├─ readCaseDetail  ──GET──▶  n8n webhook
  └─ pushResolution  ──POST──▶ n8n webhook
                                    │
                                    ▼
                            Salesforce Service Cloud
                          (read case + feed · write Resolution_Summary__c)
```

The GPT calls a single n8n webhook at `https://advantive.app.n8n.cloud/webhook/case-resolution/summary`. n8n handles Salesforce auth, SOQL queries, and write-back — this routes around the ChatGPT↔Salesforce connector access issues the team hit earlier.

**Files:**
| File | Purpose |
|------|---------|
| `engineer-tool/instructions.md` | Full GPT system prompt — paste into the ChatGPT Configure tab |
| `engineer-tool/openapi-schema.json` | OpenAPI 3.1 schema for the GPT Action (GET read + POST write) |
| `engineer-tool/gpt-logo.png` | Logo image used in the ChatGPT GPT profile |
| `n8n-case-resolution-workflow.json` | n8n workflow — import into Advantive's n8n instance to stand up the Salesforce backend |

**Resolution output format** (the block saved to Salesforce — customer-visible):
```
Inquiry: <what the customer reported>
Root Cause: <why it happened; "Not conclusive" if undetermined>
Solution: <concrete steps that resolved it>
How to Prevent It From Happening Again: <deflection; "NA" if nothing>
```
A tech-only section is shown in the chat (case research notes, customer type, prior reference case numbers, confidence level) but is never saved to Salesforce.

**How to rebuild the GPT:**
1. ChatGPT → **My GPTs** → **Create** → **Configure** tab
2. Paste `engineer-tool/instructions.md` into the Instructions field
3. Under **Actions** → **Create new action** → paste `engineer-tool/openapi-schema.json`
4. Set authentication to the header secret configured in the n8n workflow

---

## Tool 2 — Case Analyzer / Sentiment GPT (Planned)

Reads all cases closed in a rolling window → scores each Positive / Neutral / Negative → surfaces negatives + case numbers so QA reviews 5 not 50. Jaime helps define scope.

---

## Tool 3 — Historical Resolution Finder (Planned)

Given a case number, searches all closed cases for the same product for a known resolution. Scope TBD with Mark.

---

## Cross-cutting constraints

- Salesforce **2,000-record limit** — scope all historical searches by support product (DDI / D1 / CommSense / InfinityQS / Kiwiplan…)
- History window: **2 years default**, widen only if nothing found
- **Read-only** except for the single confirmed `pushResolution` write-back
- Foreign-language cases: read/analyze natively, write resolution in English by default

## `_old-gpt-backup/`

Paste old GPT instructions here before deleting them in ChatGPT (reusable tone / guardrails).

---

_Last updated: 2026-07-21_
