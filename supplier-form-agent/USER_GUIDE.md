# Supplier Form Agent — User Guide

**Audience:** Molly Gough and the Finance Operations team
**Last updated:** 2026-07-27

---

## What It Does

The Supplier Form Agent fills out customer vendor and supplier onboarding forms automatically using Advantive's company data. You upload the blank form; the agent fills in Advantive's legal name, tax ID, banking details, contact information, and authorized signature, then returns a completed PDF ready to send back to the customer.

No manual re-keying required.

---

## Where to Access It

ChatGPT (Enterprise) → **My GPTs** → **Supplier Form Agent**

If you do not see it, ask Business Systems to share the GPT with your account.

---

## How to Use It

### Step 1 — Open a new conversation

Start a new chat with the Supplier Form Agent.

### Step 2 — Upload the form

Attach the form file to the chat. Supported formats:

- PDF (fillable or flat/scanned)
- Excel (.xlsx)
- Word (.docx)

No additional message is needed. The agent fills the form the moment it receives the file.

### Step 3 — Download the completed PDF

The agent returns a completed PDF as a downloadable attachment, along with a brief summary of:
- which fields were filled
- which fields were left blank and why
- any layout or conversion notes to review

### Step 4 — Review and send

Open the PDF, confirm the fields look correct, and send it back to the customer via your normal process. Closing the Salesforce case remains a manual step.

---

## What Gets Filled Automatically

The agent fills every standard vendor/supplier form field using Advantive's canonical company profile, including:

- Legal entity name (Advantive LLC by default)
- Federal Tax ID / EIN
- Banking and payment information
- Business address
- Contact name and phone/email
- Authorized signature (Joy Jones's signature image)
- Printed name: Joy Jones
- Title: Collector
- Date: today's date

If a field on the form has no match in Advantive's profile, it is left blank and noted in the summary.

---

## Common Scenarios

### Standard fillable PDF

Attach the PDF. The agent reads the form fields, fills them from Advantive's profile, flattens the form, and returns the completed PDF.

### Flat or scanned PDF (no form fields)

Attach the PDF. The agent locates label positions visually, overlays the correct values, and returns the completed PDF.

### Excel vendor form

Attach the .xlsx file. The agent identifies the supplier onboarding sheet, fills in the answer cells adjacent to each label, and exports the result as a PDF.

### Word vendor form

Attach the .docx file. The agent fills the form fields or table cells and exports the result as a PDF.

### Form for a different Advantive entity

If the form is for an Advantive entity other than Advantive LLC (e.g., a subsidiary), the agent will ask you to confirm which entity. It fills from that entity's data if it is in the profile.

---

## Common Issues

| Symptom | What to do |
|---------|-----------|
| Agent asks a question instead of filling immediately | This happens only if a required file is missing from its Knowledge or the file is genuinely unreadable. Reply with the clarification it requests. |
| A field that should be filled is blank | Check the summary — the agent explains which fields it could not match. If the field is important, contact Business Systems to update the supplier profile. |
| Signature is missing from the PDF | The agent only adds the signature when a clear signature section is present. If your form has one but the signature is missing, report to Business Systems. |
| Banking information looks incorrect | Contact Finance Operations immediately — `advantive_supplier_profile.json` may need to be updated by the file custodian. Do not send the form until the data is verified. |
| PDF layout is off (overlapping text, wrong position) | Note the specific field and form name, and report to Business Systems for a fix. |

---

## Tips

- You do not need to type any instructions — attaching the file is enough to trigger the agent.
- Always review the completed PDF before sending. The agent is accurate but form layouts vary; a quick visual check prevents errors.
- The agent handles one form per message. For multiple forms, upload them one at a time in separate messages.
- Date fields are always filled with today's date. If you need a specific date, let the agent finish and then manually update that field in the PDF.
