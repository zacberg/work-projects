# Demand Letter Agent — Technical Documentation

**Last updated:** 2026-07-27
**Built by:** Zach Bergman (Business Systems intern)
**Status:** Live — in active use by Jordan Duke and collections leadership

---

## Overview

The Demand Letter Agent is a ChatGPT Custom GPT that drafts professionally formatted, legally appropriate demand and termination letters for Advantive's AR collections team. It pulls customer and invoice data from NetSuite (with Salesforce as a fallback) and produces completed PDF letters ready for Jordan Duke or collections leadership to review and send. Letters are never sent automatically — the agent operates in shadow mode throughout.

---

## Architecture

| Component | Detail |
|-----------|--------|
| Platform | ChatGPT Custom GPT |
| Model | GPT-4o (ChatGPT Enterprise) |
| Capabilities | Code Interpreter / file generation (PDF output) |
| Live system connections | NetSuite (primary), Advantive Salesforce (fallback) |
| Knowledge files | `Bodycote Demand.pdf` — master reference letter for branding, layout, signature, and approved wording |
| Shadow mode | All letters are drafted for human review; none are sent or filed automatically |

---

## Data Sources

| Source | Purpose | How it is accessed |
|--------|---------|-------------------|
| NetSuite | Customer legal name, billing address, contact name, contact email, invoice numbers, total balance due | GPT Actions connector — transaction-first lookup path |
| Advantive Salesforce | Customer and contact fallback when NetSuite is incomplete or returns no result | GPT Actions connector — used only when NetSuite is insufficient |
| `Bodycote Demand.pdf` (Knowledge) | Governing formatting reference — Advantive logo, signature image, Times New Roman styling, Jordan Duke wording | Uploaded to GPT Knowledge |
| User chat input | Customer name, account number, or batch list to trigger letter generation | Pasted directly into the chat at runtime |

The agent never fabricates invoice numbers, balances, addresses, or contact details. If required data cannot be found in NetSuite or Salesforce, it pauses only the affected entry and asks Jordan for the missing field.

---

## Workflow

1. Jordan pastes one or more customer names or account numbers into the chat.
2. The agent looks up each customer in NetSuite using the transaction-first lookup path, collecting: legal name, billing address, primary contact, all active invoice numbers, and total amount due.
3. If NetSuite is missing data for a specific customer, the agent falls back to Salesforce for contact details only. Invoice numbers and balances always come from NetSuite.
4. For each resolved customer, the agent generates a completed demand letter PDF:
   - Branding, layout, signature image, logo, and Jordan Duke's exact wording are preserved from `Bodycote Demand.pdf`.
   - Only customer-specific fields change: date, recipient address, contact name, invoice numbers, and total amount due.
5. Completed PDFs are returned in the chat as downloadable files.
6. If a contact name cannot be confirmed from the source systems, the agent infers the most likely name, flags it explicitly for manual review, and still generates the letter.
7. In batch requests, letters for resolved customers are delivered immediately without waiting for blocked entries.

---

## Letter Generation Rules

- Template master: `Bodycote Demand.pdf` — all branding, layout, font (Times New Roman), logo placement, and signature image are preserved exactly.
- The ATTN: line is always present. If a contact name is available, it follows ATTN:. If not, the line is left blank after ATTN:.
- Multi-page PDFs use standard top-of-page placement on continuation pages — no large blank gaps or vertically centered carryover text.
- The agent performs a lightweight quality check on each PDF (branding assets present, customer fields inserted, no malformed page flow) but does not run a full visual pass unless a concrete quality issue is detected.

---

## Repo Structure

| File / Folder | Purpose |
|---------------|---------|
| `instructions.md` | Full GPT system prompt — paste into Configure → Instructions to rebuild |
| `config.md` | GPT name, description, conversation starters, connected apps, and capabilities |
| `knowledge-base/Bodycote Demand.pdf` | Master reference letter uploaded to GPT Knowledge |
| `README.md` | Project overview and rebuild steps |

> ChatGPT Custom GPTs have no exportable code. This repo is the version-controlled source of truth for all configuration so the GPT can be rebuilt or audited without depending on one person's ChatGPT account.

---

## How to Rebuild the GPT

1. Log in to ChatGPT (Enterprise) → **My GPTs** → **Create** (or Edit the existing GPT) → **Configure** tab.
2. Set **Name** and **Description** from `config.md`.
3. Paste the full contents of `instructions.md` into the **Instructions** field.
4. Add the **Conversation starters** from `config.md`.
5. Upload `knowledge-base/Bodycote Demand.pdf` to **Knowledge**.
6. Enable **Code Interpreter** under Capabilities.
7. Attach the **NetSuite** and **Advantive Salesforce** Actions connectors (confirm exact connector names from the Configure → Apps tab of the working GPT before rebuilding).

---

## Maintenance and Support

| Task | Steps |
|------|-------|
| Update letter wording or formatting | Replace `Bodycote Demand.pdf` in Knowledge with the revised example; update `instructions.md` if any generation rules change; re-upload to the GPT |
| Add or update a connected app (NetSuite schema change) | Update the relevant GPT Actions connector; test with a known customer account |
| Update the GPT system prompt | Edit `instructions.md` in this repo → commit → paste updated content into Configure → Instructions in ChatGPT |
| Transfer ownership to another ChatGPT account | Rebuild the GPT from this repo using the steps above; no state is stored in the GPT beyond the files in this repo and the Knowledge uploads |

---

## Known Issues and Limitations

| Issue | Detail |
|-------|--------|
| No exportable GPT code | ChatGPT does not allow exporting a Custom GPT. This repo is the only durable backup of configuration. Keep it current after any Configure-tab change. |
| Contact name inference | When NetSuite and Salesforce both lack an explicit contact name, the agent infers from available signals (e.g., email format). These letters are flagged for Jordan to manually verify before sending. |
| Batch size | No formal batch size limit is enforced, but very large batches may hit ChatGPT session context limits. Process in sub-batches if needed. |
| Actions connector names | `config.md` notes that connector names should be confirmed from the live GPT's Apps tab. If the NetSuite or Salesforce connector is renamed or replaced, `config.md` should be updated accordingly. |
| Shadow mode only | The agent drafts letters but does not send, file, or update any records. Sending remains a manual step performed by Jordan or collections leadership. |
