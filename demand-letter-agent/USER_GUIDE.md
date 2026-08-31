# Demand Letter Agent — User Guide

**Audience:** Jordan Duke and Advantive collections leadership
**Last updated:** 2026-07-27

---

## What It Does

The Demand Letter Agent drafts past-due demand letters for customers who are significantly delinquent on their AR balances. You provide one or more customer names or account numbers; the agent looks up their invoice data in NetSuite, fills in Advantive's approved letter template, and returns ready-to-review PDF letters.

The agent never sends letters automatically. Every letter is reviewed and sent by you or collections leadership.

---

## Where to Access It

ChatGPT (Enterprise) → **My GPTs** → **Demand Letter Agent**

If you do not see it, ask Business Systems to share the GPT with your account.

---

## How to Use It

### Step 1 — Start a new conversation

Open the Demand Letter Agent from My GPTs.

### Step 2 — Paste in your customer list

Type or paste one customer name, one account number, or a list of multiple customers. Examples:

```
Acme Manufacturing
```

```
Acme Manufacturing, Consolidated Freight Inc, Widget Co
```

```
Account 1047382
```

No special formatting is required. The agent accepts customer names and account numbers in any order.

### Step 3 — Wait for the PDFs

The agent queries NetSuite for each customer's invoices and balance, then generates a completed demand letter PDF. For batch requests, letters for customers whose data is found are returned immediately — you do not have to wait for the full batch to finish.

### Step 4 — Review and send

Download each PDF, verify the customer details (name, address, contact, invoice numbers, total due), and send via your normal collections process. The agent flags any letter where it inferred a contact name — those require a manual contact-name check before sending.

---

## Common Scenarios

### Single customer

Paste the customer name or account number. The agent returns one PDF.

### Batch of customers

Paste multiple names or numbers separated by commas or line breaks. The agent processes them in parallel and returns PDFs as each one is resolved.

### Customer not found in NetSuite

The agent tries Salesforce as a fallback. If the customer still cannot be found, it tells you exactly what is missing and asks for the specific field. Provide the missing detail and it generates the letter.

### Contact name is unknown

If neither NetSuite nor Salesforce has a confirmed contact name, the agent infers the most likely name and explicitly flags the letter for contact-name verification. Review the name before sending.

### Customer data is correct but you need a different invoice listed

After the agent generates the letter, reply in the same chat with the correction (e.g., "Use invoice INV-10042 instead of INV-10039 for Acme"). The agent will regenerate.

---

## What the Agent Will Not Do

- Send letters on your behalf
- Answer questions about collections strategy, legal advice, or account history beyond what is needed to draft a letter
- Change the legal language or Advantive contact information in the approved template
- Use invoice data from any source other than NetSuite (Salesforce is used only for contact and address details when NetSuite is incomplete)

If you ask the agent to do something outside letter drafting, it will redirect you.

---

## Common Issues

| Symptom | What to do |
|---------|-----------|
| Agent cannot find the customer | Check the spelling or provide the NetSuite account number; if the customer is very new, it may not yet have invoices in NetSuite |
| Letter shows wrong invoice total | Verify in NetSuite that the invoices are marked active/open; reply in chat with the correct data and the agent will regenerate |
| Contact name is missing or wrong | Reply with the correct contact name; the agent will regenerate with the confirmed name |
| PDF branding looks wrong (no logo or signature) | Report to Business Systems — the Knowledge file may need to be re-uploaded |
| GPT is not responding or errors out | Refresh the ChatGPT session and try again; if it persists, contact Business Systems |

---

## Tips

- For recurring batches (e.g., end-of-month dunning), paste the full list at once — the agent handles parallel processing.
- Always review flagged letters (inferred contact name) before sending.
- The agent preserves Jordan Duke's exact approved wording; do not ask it to rewrite the legal language.
- Keep customer names consistent with how they appear in NetSuite to get the fastest match.
