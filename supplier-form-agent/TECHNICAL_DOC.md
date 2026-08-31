# Supplier Form Agent — Technical Documentation

**Last updated:** 2026-07-27
**Built by:** Zach Bergman (Business Systems intern)
**Status:** Live — deployed as a ChatGPT Custom GPT; active handoff to Molly Gough (Finance Operations) in progress

---

## Overview

The Supplier Form Agent is a ChatGPT Custom GPT that auto-fills customer vendor and supplier onboarding forms with Advantive's canonical company data and returns a completed, signed PDF. Finance Operations receives approximately 50 of these forms per month via Salesforce; previously each one required manual re-keying. The agent eliminates that by filling every form automatically from a single JSON source of truth.

Default behavior: the moment a file is attached, the agent fills it and returns a completed PDF with no prompting, no menus, and no clarifying questions.

---

## Architecture

| Component | Detail |
|-----------|--------|
| Platform | ChatGPT Custom GPT |
| Model | GPT-4o (ChatGPT Enterprise) |
| Capabilities | Code Interpreter (required — used for all PDF/Excel/Word processing) |
| Live system connections | None — operates entirely from uploaded files |
| Knowledge: company data | `advantive_supplier_profile.json` — single source of truth for all Advantive company, tax, banking, legal, and contact values |
| Knowledge: signature | `joy_jones_signature.png` — applied to authorized signature lines |
| Default signing entity | Advantive LLC |
| Default signer name | Joy Jones |
| Default signer title | Collector |

---

## Runtime Libraries (Code Interpreter)

The agent uses Python inside Code Interpreter to process and produce files:

| Library | Purpose |
|---------|---------|
| `pypdf` | Read AcroForm field names in fillable PDFs |
| `PyMuPDF` (fitz) | Locate label positions in flat/scanned PDFs; overlay values; export PDF |
| `pdfplumber` | Additional PDF parsing as needed |
| `python-docx` | Fill Word form fields and tables; export to PDF |
| `openpyxl` | Read label cells in Excel workbooks; write adjacent answer cells |
| `reportlab` | PDF generation and overlay rendering |

---

## Input Format Handling

| Input format | Processing approach |
|-------------|-------------------|
| Fillable PDF (AcroForm) | Read AcroForm field names → map to supplier profile → fill → flatten → export PDF |
| Flat or scanned PDF | Locate each label by position → overlay the matching value near its answer area → export PDF |
| Excel (.xlsx) | Identify the supplier-onboarding sheet → find each label cell → write the matching value into the adjacent answer cell → export as PDF |
| Word (.docx) | Fill form fields and tables → export as PDF |

All formats return a single completed PDF regardless of the original format.

---

## Field Mapping Logic

1. Every value comes from `advantive_supplier_profile.json`. Nothing is invented or guessed.
2. Field labels are matched to profile keys using the field name, common aliases, and close business synonyms (e.g., EIN, Federal Tax ID, and TIN are treated as the same field).
3. If a label has no confident match in the profile, the field is left blank and the gap is noted in the post-delivery summary.
4. The job is never abandoned over a single missing field — the agent completes everything it can and reports what it could not fill.

---

## Signature, Date, and Title Rules

| Field type | Behavior |
|------------|---------|
| Authorized Signature | `joy_jones_signature.png` applied only when a clear signature section or signature line exists |
| Date fields | Always set to today's date in MM/DD/YYYY format |
| Printed name | "Joy Jones" |
| Title (Vendor Contact Title, Authorized Signer Title, etc.) | "Collector" |
| Forms with no signature section | Signature image is omitted |

---

## Knowledge Files (Not in Repo)

`advantive_supplier_profile.json` and `joy_jones_signature.png` are uploaded directly to the GPT's Knowledge in ChatGPT. They are intentionally excluded from this repo because they contain sensitive company banking and tax information.

To update either file:
1. Obtain the updated version from Finance Operations (Molly Gough) or the file custodian.
2. Go to the GPT → Configure → Knowledge → remove the old version → upload the new version.
3. Test with a sample form before notifying Molly that the update is live.

---

## Repo Structure

| File | Purpose |
|------|---------|
| `instructions.md` | Full GPT system prompt — paste into Configure → Instructions to rebuild |
| `USER_STORY.md` | Requirements and acceptance criteria |
| `README.md` | Project overview, rebuild steps, and scope notes |

---

## How to Rebuild the GPT

1. Log in to ChatGPT (Enterprise) → **My GPTs** → **Create** → **Configure** tab.
2. Paste the full contents of `instructions.md` into the **Instructions** field.
3. Upload `advantive_supplier_profile.json` to **Knowledge** (obtain from Finance Operations — not stored in repo).
4. Upload `joy_jones_signature.png` to **Knowledge** (obtain from Finance Operations — not stored in repo).
5. Enable **Code Interpreter** under Capabilities.
6. Test with a sample supplier form before handing off to Molly Gough.

---

## Maintenance and Support

| Task | Steps |
|------|-------|
| Update Advantive company data (address, banking, tax ID change) | Get updated `advantive_supplier_profile.json` from Finance Operations → re-upload to Knowledge |
| Update or replace the authorized signature | Get updated `joy_jones_signature.png` → re-upload to Knowledge |
| Change the default signer or title | Edit the relevant lines in `instructions.md` → commit to repo → re-paste into Configure → Instructions |
| GPT not filling a new form format correctly | Check if the form is AcroForm or flat; if flat, the overlay approach may need coordinate tuning — report to Business Systems |

---

## Scope and Limitations

| Item | Detail |
|------|--------|
| Default entity | Advantive LLC. Other Advantive entities are supported only if they appear in `advantive_supplier_profile.json`. |
| Submission and case closure | The agent returns the completed PDF; submitting it to the customer and closing the Salesforce case remain manual steps. |
| No live system access | The agent does not connect to Salesforce, NetSuite, or any external system. It works from the uploaded profile and the form provided in the chat. |
| Sensitive data exposure | `advantive_supplier_profile.json` contains banking and tax information. Treat the GPT's Knowledge as sensitive. Do not share the profile JSON outside of Finance Operations and Business Systems. |
