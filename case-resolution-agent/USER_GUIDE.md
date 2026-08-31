# Case Resolution Summary Generator — User Guide

**For:** Rashtin and the support tech team  
**Last updated:** 2026-07-27

---

## What is this tool?

The Case Resolution Summary Generator is a ChatGPT tool built specifically for the Advantive support team. You give it a case number, it pulls the case details and email thread directly from Salesforce, drafts a resolution in the team's standard format, and — after you review and approve it — saves the text directly to the case's Resolution Summary field in Salesforce.

No more copying the entire email thread into ChatGPT by hand. No more formatting the four sections yourself. The tool does both.

---

## Where to find it

1. Open [ChatGPT Enterprise](https://chatgpt.com) and sign in with your Advantive account.
2. In the left sidebar, click **My GPTs** (or **Explore GPTs**).
3. Find **Case Resolution Summary Generator** and open it.

If you use it regularly, pin it to your sidebar for quick access.

---

## How to use it

### Step 1 — Give it a case number

Type the case number into the chat. You can use any of these formats:

- `00786393`
- `Case 00786393`
- A Salesforce case URL (paste the full URL and the tool will extract the case number)
- A customer or account name (the tool will show you a list of open cases to pick from)

One case at a time only. If you give multiple numbers, the tool will ask which one to start with.

### Step 2 — Review the case header

The tool pulls the case from Salesforce and shows you a header block first. This is for your reference — it is never saved to Salesforce. It looks like this:

```
Generated: 07/27/2026
Case 00786393 (Acme Corporation)
Priority: High
Business Unit: DDI
Support Product: D1
ADO Work Item ID: N/A
Dev Issue #: N/A
Opened: 06/15/2026
Last activity: 07/20/2026
Resolved/closed: 07/25/2026
Days open: 40
```

Check this against the case in Salesforce to confirm the tool pulled the right record before continuing.

### Step 3 — Review the draft resolution

Below the header, the tool drafts the four-section resolution. Review each section carefully. The draft is based entirely on the case fields and email thread — double-check that it accurately reflects what actually happened.

You can ask the tool to revise any section by typing what you want changed. For example:

- `The root cause was actually a misconfigured API key — can you update How It Was Resolved?`
- `Remove the mention of the workaround in Additional Considerations.`
- `The How to Prevent section should mention validating the license before setup.`

Keep revising until the draft is accurate and customer-ready.

### Step 4 — Confirm to save

When the draft is ready, the tool will say:

> `Ready to save this to Salesforce — want me to push it?`

Type **yes** (or anything confirming). The tool will call Salesforce and save the text to the Resolution Summary field on the case.

You will see one of two responses:

- `Resolution summary saved.` — The save went through. You are done.
- `The push didn't go through — please paste it into the Resolution tab manually.` — Something failed. The tool will show you the full text to copy. Paste it into the Resolution Summary field in Salesforce manually.

---

## The four sections explained

The resolution is saved as four labeled sections. Here is what each one is for:

**Query**
A short, clear summary of what the customer reported — their issue or question in plain language. This is customer-facing, so write (or confirm) it as if the customer will read it.

**How It Was Resolved**
The specific steps, configuration changes, or fixes that actually solved the problem. Be concrete — what was done, not just "the issue was resolved." If the resolution could not be determined, this section will say `Not conclusive`.

**Additional Considerations**
Supplemental context: root cause analysis if known, workarounds that were tried, related background, or anything useful for understanding the full picture. If there is nothing to add, this section says `NA`.

**How to Prevent it from happening again**
Guidance that would prevent the same issue from recurring — a setup check, a configuration to validate before go-live, a documentation note to share. If there is no actionable prevention guidance, this section says `NA`.

---

## What does N/A mean in the header?

Some fields on a case are optional or may not be filled in. If the tool cannot find a value for a field, it shows `N/A` rather than leaving the line blank. This is expected for fields like:

- **ADO Work Item ID** — only populated if a dev ticket was linked to the case
- **Dev Issue #** — only populated if an engineering issue was logged
- **Resolved/closed** — blank on cases that are still open

`N/A` is not an error. It means the field was empty in Salesforce.

---

## Common issues

### "Case not found" or the tool asks you to double-check the number

The case number did not match any record in Salesforce. Try these steps:
1. Check that you copied the full case number (it should be 8 digits, e.g., `00786393`).
2. Make sure you are searching for a case that exists in Salesforce (not a Zendesk or external ticket).
3. If the number looks right and the tool still cannot find it, let Zach know — there may be a Salesforce permissions issue.

### Fields in the header are showing N/A when they should have values

Some fields are legitimately empty on many cases (ADO Work Item ID, Dev Issue #). For other fields that you know are populated in Salesforce, this could mean the field was not returned by the lookup. Try running the case again. If it keeps happening on the same case, let Zach know so the field can be added to the data pull.

### "The push didn't go through"

The save to Salesforce failed. The tool will display the full resolution text when this happens. Copy it and paste it directly into the Resolution Summary field in the case in Salesforce. Then let Zach know so the connection can be checked.

The most common cause is a temporary issue with the n8n-to-Salesforce connection. If it keeps happening across multiple cases, contact Zach or Jaime Rennick (Business Systems).

### The draft looks wrong or made something up

The tool only uses information from the case record and email thread. If a section looks off, it may be grounding a detail from an early email that was later corrected. Ask the tool to revise with the correct information before saving. Never approve a draft that does not accurately reflect what happened — the saved text is customer-facing.

---

## A few things to keep in mind

- The tool shows a **tech-only section** at the bottom of its response (labeled `FOR TECH ONLY`). This includes case research notes, customer type, and confidence level. This section is never saved to Salesforce — it is for your reference only.
- The tool will not save anything without your explicit confirmation. You are always in control.
- The four-section block that gets saved is customer-visible. Exclude internal names, internal emails, engineering jargon, blame, speculation, and any information that should not be shared with the customer. The tool is instructed to exclude these, but you are the final check.
- If you get a case in a foreign language, the tool can read and analyze it. The resolution will be drafted in English by default unless you ask for another language.
