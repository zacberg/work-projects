# Collections Agent — User Guide

**For:** Jordan Duke and the AR Collections Team  
**Last updated:** 2026-07-27

---

## What is the Collections Agent?

The Collections Agent is a ChatGPT assistant built specifically for the Advantive AR Collections team. It helps you quickly pull up account information, draft collection emails, generate reports, and work through common collections tasks — without leaving ChatGPT.

The agent connects live to NetSuite and Salesforce to pull current AR data, so you are always working from real numbers, not stale exports.

**Important:** The agent is a drafting and analysis tool. It does not send emails, update records in Salesforce or NetSuite, place accounts with agencies, or make any changes in any system. Every email it produces is a draft for you to review. Every recommendation requires your sign-off before any action is taken.

---

## How to Access It

1. Log in to **ChatGPT Enterprise** at [chat.openai.com](https://chat.openai.com) with your Advantive account.
2. Open **My GPTs** from the left sidebar (or use the direct link your admin shared).
3. Select **AR Collections Agent**.
4. Start a new chat and type your request.

You do not need to install anything. The agent is available to all collections team members with ChatGPT Enterprise access.

---

## What It Helps With

The agent covers 11 workflows the collections team runs regularly:

| What you need | What to ask for |
|---------------|----------------|
| Pull up a customer's full AR status | "Give me a status summary for [Account Name]" |
| See who is 60+ days past due | "Show me accounts over 60 DPD" |
| Draft a collections email | "Draft a collections email for [Account Name]" |
| Run the daily cash update | "Build today's cash update email" |
| Check if an account is eligible for third-party placement | "Run the placement tracker" |
| Review support holds | "Run the support hold audit" |
| Check an account for legal restrictions before contacting | "Run a legal check on [Account Name]" |
| Review payment plan risk | "Review payment plans for broken promise risk" |
| Draft a demand or termination letter | "Draft a demand letter for [Account Name]" |
| Check portal / billing case backlog | "Run the portal submission tracker" |
| Review write-off candidates | "Show me write-off candidates" |
| Clean up or rewrite a SOP | "Help me rewrite this SOP" |

---

## Example Requests

Here are specific things you can type to the agent:

**Look up an account:**
> "Pull up the AR status for Acme Corp — I need their balance, DPD, whether there's a hold, and their CSM."

**Check overdue balances:**
> "Give me the list of accounts over 90 days past due with balances over $5,000."

**Draft a collections email:**
> "Draft a collections email for [Account Name]. They're at 75 DPD with a $12,000 balance. Firm but professional tone."

**Run the daily cash update:**
> "Build today's cash update email with the Go Get number."

**Run the placement tracker:**
> "Run the third-party placement tracker and show me the TAA-ready accounts."

**Check legal status before contacting:**
> "Run a legal check on [Account Name] before I draft their demand letter."

**Get a demand letter:**
> "Draft a demand letter for [Account Name] — pull the invoice detail from NetSuite."

**Check support holds:**
> "Run the support hold audit — show me holds that should be released and any accounts that should have a hold applied."

**Write-off candidates:**
> "Show me write-off candidates at 180+ DPD."

---

## Where the Data Comes From

The agent pulls live data from the same systems you work in:

| Data | Source |
|------|--------|
| Invoice balances, DPD, aging | NetSuite (live) |
| Support holds, CSM name, legal flags, open opportunities | Salesforce (live) |
| Prior emails / outreach history | Outlook (live) |
| AR Tracker, weekly cash target, top aged accounts | SharePoint (live) |
| Strategic account list (do-not-contact) | SharePoint (live — always the latest version) |
| SOPs, email templates, escalation procedures | Uploaded knowledge files |

**NetSuite is always the authority on balances and invoice details.** If NetSuite and Salesforce disagree on a balance, the agent uses the NetSuite number.

Before drafting any customer-facing email, demand letter, or termination letter, the agent automatically checks the live strategic account list. If the account is on that list, the agent will flag it as a strategic restriction and will not draft auto-contact — you will need to route it to internal review instead.

---

## What It Cannot Do

**The agent does not:**
- Send emails on your behalf
- Update Salesforce records (holds, placement flags, opportunity stages)
- Modify NetSuite records or invoices
- Place accounts with TAA — placement recommendations are for your review only
- Approve write-offs — those go through Justin Wixom and Joy Jones
- Access YayPay — promises-to-pay data in the daily cash update is a manual input gap

**The agent does not have access to:**
- YayPay dunning history — if you want to know what automated emails have already gone out, check YayPay directly before asking the agent to draft a follow-up
- Real-time payment processing
- NetSuite customer setup records (only invoice-level data)

**Promises-to-Pay (Feature 3):** YayPay is not connected, so the agent cannot automatically pull your promises-to-pay number. If you have that number handy, paste it in and the agent will use it in the Go Get calculation. Otherwise it will flag it as missing.

**Tuesday checks in transit:** The historical source for this number (Josh Snow) is no longer at Advantive. The agent will flag this as an unconfirmed source — you will need to confirm the current source before including that figure.

---

## Tips for Getting the Best Results

- **Name the account** whenever possible. "Status summary for Windstream" gets much faster results than "pull up an account."
- **State the workflow** you need. "Run the placement tracker" or "draft a demand letter" is more specific than "help me with this account."
- **Paste context if data is missing.** If a connector is not returning data for some reason, you can paste in a NetSuite export or Salesforce record and the agent will work with that.
- **One workflow at a time** produces cleaner output. If you need both a placement check and an email draft, you can ask for both in one message — the agent will combine them — but starting with the legal check first helps keep things clean.
- **Review every draft before sending.** The agent produces its best single draft based on the data it can see. Check balances, contact names, and tone before sending any email.

---

## If Something Is Not Working

**The agent says it cannot reach NetSuite or Salesforce:**  
The connector may need to be re-authenticated. Contact Business Systems (Jaime) or the ChatGPT Enterprise admin to refresh the connection.

**Balances look wrong or much higher than expected:**  
This is most commonly a query-scope issue on the backend. Let Zach Bergman know — the query may need a filter correction.

**An account is missing from a report:**  
The agent applies a default limit of 500 records per Salesforce query. For very large portfolio scans, some accounts may not appear. Ask by specific account name if you need a result for an account you expected to see.

**The agent is including a former employee's name:**  
Kevin Boyce, Jeremy Van Beusekom, Jeffery Bartels, and Josh Snow no longer work at Advantive. The agent is configured to exclude them, but if one appears in an output, remove it manually and let Zach know so the configuration can be updated.

**General questions or issues:**  
Contact Jordan Duke for collections workflow questions. Contact Zach Bergman for agent configuration or technical issues.

---

## Contacts

| Name | Role |
|------|------|
| Jordan Duke | AR Sr Manager — collections questions, workflow guidance |
| Zach Bergman | Builder — agent configuration, technical issues, connector problems |
| Business Systems (Jaime) | Salesforce / connector access issues |
| Justin Wixom | Write-off approvals |
| Joy Jones | Write-off approvals |
| Tiffany Johnson | Billing Ops escalations |
