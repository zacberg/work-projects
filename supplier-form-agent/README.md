# Supplier Form Agent

A ChatGPT Custom GPT that auto-fills customer vendor and supplier onboarding forms with Advantive's canonical company information and returns a completed, signed PDF. Built for Molly Gough (Finance Operations).

Built by Zach Bergman (2026 summer intern, Business Systems).

**Status: Live.** The agent is deployed as a ChatGPT Custom GPT and available for use by the Finance Operations team. Active testing and handoff to Molly Gough is in progress following her return from PTO.

---

## What it does

Customers send Advantive vendor setup and supplier onboarding forms in various formats (fillable PDF, scanned PDF, Excel, Word). Finance Ops previously filled each one manually, re-keying the same Advantive tax, banking, legal, and contact information every time — approximately 50 forms per month via Salesforce.

The agent automates this: upload the form, and the agent fills it with the correct Advantive data from a canonical supplier profile, applies the authorized signature, and returns a completed PDF.

**Default behavior:** when a file is attached, the agent immediately fills it and returns a PDF. No clarifying questions, no menus, no analysis — just the completed form.

---

## How it works

| Input format | Approach |
|-------------|---------|
| Fillable PDF (AcroForm) | Reads field names, maps to profile, fills, flattens, exports PDF |
| Flat or scanned PDF | Locates each label position, overlays the value next to it, exports PDF |
| Excel (.xlsx) | Finds each label cell, writes Advantive's value into the adjacent answer cell, renders to PDF |
| Word (.docx) | Fills form fields and tables, exports to PDF |

Every value comes from advantive_supplier_profile.json — the single source of truth for Advantive's company, tax, banking, legal, and contact information. Nothing is invented or guessed.

The signature (joy_jones_signature.png) is applied to the Authorized Signature line automatically. Date fields are set to today's date. Printed name is "Joy Jones". Title is "Collector".

Fields with no confident match are left blank and noted in the summary — the job is never abandoned over a single missing field.

---

## Repo structure

| File | Purpose |
|------|---------|
| `supplier_form_gpt_instructions.md` | Full GPT system prompt — paste into the ChatGPT Configure tab |
| `USER_STORY.md` | Requirements and acceptance criteria |

The advantive_supplier_profile.json and joy_jones_signature.png files are uploaded to the GPT's Knowledge in ChatGPT and are not stored in this repo (they contain sensitive company and banking information).

---

## How to rebuild the GPT

1. ChatGPT -> **My GPTs** -> **Create** -> **Configure** tab
2. Paste supplier_form_gpt_instructions.md into the Instructions field
3. Upload advantive_supplier_profile.json and joy_jones_signature.png to **Knowledge**
4. Enable **Code Interpreter** (required for PDF generation)

---

## Scope and limitations

- Default entity is Advantive LLC. Other Advantive entities are supported only if present in the supplier profile.
- The agent returns the completed PDF; submitting it back to the customer or closing the Salesforce case remains manual.
- The agent does not access Salesforce or any external system — it works entirely from the uploaded profile and the form the user provides.

---

_Last updated: 2026-07-20_