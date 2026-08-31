# Demand Letter Agent — GPT configuration

> Backup of the ChatGPT custom GPT / agent's Configure settings.
> Captured 2026-06-04.

## Identity
- **Name:** Demand Letter Agent
- **Description:** Generates demand letters from NetSuite overdue accounts

## Conversation starters
- **Create demand letter** — Generate one from an account lookup.
- **Check overdue balance** — Find invoices before drafting.

## Instructions
Full text in [`instructions.md`](instructions.md).

## Connected apps / Actions
- **NetSuite** — primary system of record for customer + invoice data (transaction-first lookup).
- **Advantive Salesforce** — fallback only, for customer/contact details when NetSuite is incomplete.
- _(confirm exact connector names from the agent's **Apps** tab)_

## Capabilities
- Code Interpreter / file generation (produces the demand-letter PDFs)
- _(confirm remaining checkboxes from Configure)_

## Knowledge files
- **Bodycote Demand.pdf** — the governing completed example letter; master reference for Advantive branding, layout, logo (top-left), signature image (bottom), Times New Roman styling, and Jordan Duke's wording. _(copy stored in `knowledge-base/`)_
