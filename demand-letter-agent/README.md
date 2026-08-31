# Demand Letter Agent

A ChatGPT Custom GPT built for Advantive's AR Collections team that drafts past-due demand and termination letters for delinquent customers. Built for Jordan Duke and the collections leadership team.

This repo is the version-controlled source of truth for the GPT's configuration so it can be rebuilt, audited, or handed off without depending on one person's ChatGPT account.

> ChatGPT custom GPTs have no exportable code. This repo captures the GPT's Configure-tab settings as plain files.

**Status: Live.** The agent is deployed as a ChatGPT Custom GPT and is in active use by Jordan Duke and collections leadership.

---

## Architecture

| Component | Detail |
|-----------|--------|
| Agent platform | ChatGPT Custom GPT |
| Capabilities enabled | None (no live system connections) |
| Data access | GPT Knowledge (approved letter templates, tone guidelines, SOPs) and user-supplied invoice/balance detail pasted into the chat |
| Integrations | None — shadow mode only; letters are drafted for human review and are never sent automatically |

---

## Data sources

| Source | How it reaches the agent |
|--------|--------------------------|
| Approved letter templates | Uploaded to GPT Knowledge from `knowledge-base/` |
| Tone and style guidelines | Uploaded to GPT Knowledge from `knowledge-base/` |
| Customer AR detail (balances, invoice numbers, DPD) | Pasted by the user directly into the chat at runtime |

The agent has no live connections to NetSuite, Salesforce, or any other system. All customer-specific data must be supplied by the user in the conversation.

---

## What it does

The agent drafts professional, legally appropriate demand and termination letters for customers who are significantly past due on their AR balances. It uses Advantive's approved letter templates and tone guidelines to produce letters that are ready for Jordan or a collections leader to review and send.

The agent operates in shadow mode — it drafts letters for human review and does not send them or modify any records.

---

## Repo structure

| File | Purpose |
|------|---------|
| `instructions.md` | Full GPT system prompt — paste into the ChatGPT Configure tab |
| `config.md` | GPT name, description, conversation starters, capabilities, and model settings |
| `knowledge-base/` | Files uploaded to the GPT's Knowledge (letter templates, tone examples, SOPs) |

---

## How to rebuild the GPT

1. ChatGPT -> **My GPTs** -> **Create** (or Edit) -> **Configure** tab
2. Paste the Name, Description, and Conversation starters from `config.md`
3. Paste `instructions.md` into the Instructions field
4. Upload all files in `knowledge-base/` to **Knowledge**
5. Enable the capabilities listed in `config.md`

---

_Last updated: 2026-07-20_
