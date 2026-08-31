# AR Dashboard + Pulse Deck Creator — User Guide

**For:** Jordan Duke, Justin Wixom, and Finance Operations / Collections leadership
**What this is:** A live AR collections dashboard and one-click weekly Pulse Deck generator
**Questions?** Contact Business Systems (Zach Bergman / your Business Systems team)

---

## Table of Contents

1. [Accessing the Dashboard](#1-accessing-the-dashboard)
2. [What the Dashboard Does](#2-what-the-dashboard-does)
3. [Dashboard Tabs](#3-dashboard-tabs)
   - AR Overview
   - Collections Team — 60+ DPD
   - Collections Team — Full Portfolio
   - Customer 360
   - AR Analytics
4. [Generating the Weekly Pulse Deck](#4-generating-the-weekly-pulse-deck)
5. [Uploading a YayPay Aging Report](#5-uploading-a-yaypay-aging-report)
6. [Common Questions and Troubleshooting](#6-common-questions-and-troubleshooting)

---

## 1. Accessing the Dashboard

The dashboard is hosted on Azure and accessible from any browser — no install required.

**URL:** Contact Business Systems for the current Azure URL. It was distributed to Jordan Duke and Justin Wixom when the app went live.

The dashboard runs directly in your browser. No login is required (the app is on the internal Azure deployment). Data is pulled live from Advantive's production NetSuite and Salesforce systems.

---

## 2. What the Dashboard Does

The AR Dashboard gives the Finance Operations and Collections teams a single place to see Advantive's full AR portfolio in real time, without manually running reports in NetSuite or YayPay.

**Key capabilities:**

- See the current state of all open AR — total balances, overdue amounts, 60+ DPD exposure, and cash collected this month — in one view, updated automatically every 5 minutes
- View each collections rep's assigned accounts, with 60+ DPD balances and full portfolio exposure
- Drill into any individual customer to see all open invoices, Salesforce flags (support holds, legal, CSM), and collections history
- Compare YayPay aging data against NetSuite balances side by side (by uploading a YayPay report)
- See portfolio-level trend charts: aging distribution, hold history, cash collected over time
- Generate Jordan's weekly AR Executive Pulse PPTX with one click, auto-filled with the week's data and charts

**Data sources:**
- **NetSuite** (production) — all AR balances, invoices, aging, DPD, cash collected
- **Salesforce** (production) — support holds, legal flags, CSM assignments, strategic account status
- **YayPay** — optional upload to reconcile balances (see Section 5)

---

## 3. Dashboard Tabs

### AR Overview

This is the landing page when you open the dashboard. It shows the headline numbers for the full AR portfolio:

| Metric | What it means |
|---|---|
| Total open AR | Sum of all unpaid invoices in NetSuite |
| Total overdue | All invoices past their due date |
| 60+ DPD | Invoices 60 or more days past due (the primary collections focus metric) |
| Support holds | Accounts currently on a support hold in Salesforce |
| Placement queue | Accounts flagged for external collections placement |
| Write-off pool | Balances identified as candidates for write-off |
| Cash collected MTD | Payments received so far this month |

The data refreshes automatically every 5 minutes. To pull the very latest data immediately, click the **Refresh** button in the top right. A refresh takes about 10–20 seconds.

---

### Collections Team — 60+ DPD

This tab breaks down the 60+ DPD exposure by collections rep. Each rep's card shows:
- Their total 60+ DPD balance
- The number of accounts in that bucket
- A list of the accounts with individual balances and days-past-due

Use this tab during daily standups or as the rep-level view for collections calls. Click any account name to open the Customer 360 drill-down for that account.

---

### Collections Team — Full Portfolio

This tab shows every open account assigned to each collections rep — not just those 60+ DPD. For each account you can see:
- Total open balance
- Total past-due balance

This is useful for seeing the full workload per rep and identifying accounts that may be approaching the 60+ DPD threshold before they get there.

This tab also includes the **YayPay upload** feature for reconciling YayPay balances against NetSuite. See Section 5 for how to use it.

---

### Customer 360

The Customer 360 tab opens when you click on any account name in the dashboard. It shows a real-time, live-queried view of a single customer:

- **Open invoices** — every unpaid invoice, with the invoice number, amount, due date, and current days past due
- **Salesforce flags** — support hold status, legal flag, whether the account is marked as strategic, and the assigned CSM
- **Payment history** — recent payments applied to this account
- **Collections notes** — any collections activity on record

Because this tab queries NetSuite and Salesforce live (rather than using the cached snapshot), it always reflects the current state, even if you haven't refreshed the main dashboard.

---

### AR Analytics

The Analytics tab provides portfolio-level trend charts and distributions. Use it to track how the portfolio is moving over time rather than just its current state:

- **DPD distribution** — how accounts are spread across aging buckets at any given time
- **Hold history** — how the count of support holds has changed
- **Aging trend** — movement in the 60+ DPD balance over time
- **Cash collected over time** — month-by-month cash collected view

These charts are generated from the snapshot data and refresh when the snapshot refreshes.

---

## 4. Generating the Weekly Pulse Deck

The **Generate Pulse Deck** button (in the dashboard header) builds Jordan's weekly AR Executive Pulse PPTX automatically.

### Steps

1. Open the dashboard in your browser.
2. Click **Generate Pulse Deck** in the header.
3. Wait about 15–30 seconds while the deck is built. A spinner will indicate it is working.
4. The finished `.pptx` file will download automatically to your browser's Downloads folder.
5. Open the file in PowerPoint.

### What is filled in automatically

- The week-ending date on the title slide
- All headline KPIs on slide 2 (cash MTD/QTD, attainment %, DSO, >60 balance and movement, >90 balance, holds)
- The >60 aging movement block (slide 4)
- The >90 aging movement block (slide 10)
- The top-10 past-due customer table with balances and drafted collection notes (slide 6)
- Scoreboard highlights
- Hold counts (slide 11)
- 5 cash charts: weekly run rate, quarterly run rate, cash vs. target, total cash collected, and payment methods — all generated from the AR Tracker workbook

### What still needs to be filled in manually after download

- **8 aging and risk charts** (>60 trend, >90 trend, root cause, total AR aging, upcoming-to-60, payments against >60, payments by timing %, and integrated vs. non-integrated) — these come from YayPay/Power BI and are not yet automated. They are carried forward as last week's images. Replace them with fresh screenshots as you would currently.
- **Narrative text** — the Decisions/Updates section (slide 2), Risks to Cash (slide 2), and the root-cause bullets on slide 7 are left blank for Jordan to fill in.

### Note on the AR Tracker

The deck uses the latest AR Tracker workbook to calculate cash scalars. If the current week's AR Tracker file is not available at the expected path on the server, cash figures (MTD, QTD attainment, >60 target) will appear as `—` placeholders. Contact Business Systems if this happens.

---

## 5. Uploading a YayPay Aging Report

The **Full Portfolio** tab lets you upload a YayPay aging report to compare YayPay balances against NetSuite balances side by side.

### Steps

1. Export an aging report from YayPay — either summary or detailed format, saved as a CSV.
2. Go to the **Collections Team — Full Portfolio** tab in the dashboard.
3. Drag and drop the CSV file into the upload area on that tab (or click the upload area to browse for the file).
4. The tab will update to show a new column alongside the NetSuite balances, showing the YayPay balance for the same accounts.
5. Discrepancies (where YayPay and NetSuite disagree) are highlighted so you can investigate.

The file is processed entirely in your browser — it is not sent to any server or stored anywhere. You can upload a new file at any time to update the comparison.

---

## 6. Common Questions and Troubleshooting

**The data looks old. How do I refresh it?**
Click the **Refresh** button in the top right of the dashboard. This triggers an immediate live pull from NetSuite and Salesforce. It takes about 10–20 seconds. If it fails, the dashboard will show an error message — contact Business Systems if you see a persistent error.

**The dashboard shows the wrong balance for a customer I know just paid.**
The dashboard reflects the NetSuite production data as of the last refresh. If a payment was posted very recently, click Refresh. If the payment is posted in NetSuite but the dashboard still shows the old balance after refreshing, contact Business Systems to investigate.

**The Pulse Deck downloaded but some numbers show "—" instead of a value.**
A `—` means that particular field could not be populated automatically — usually because the AR Tracker workbook file was not available when the deck was built, or the snapshot data was missing that field. Contact Business Systems to ensure the AR Tracker file is up to date on the server, then regenerate the deck.

**The Pulse Deck charts look like last week's data.**
The 8 aging/risk charts (>60 trend, root cause, etc.) are not yet automated and are carried forward from the previous deck. This is a known limitation — they still need to be replaced manually with fresh screenshots from YayPay/Power BI, the same as before. The 5 cash charts are fully automated and will always reflect the current week.

**I clicked Generate Pulse Deck and got an error.**
Wait a few seconds and try again. If the error persists, contact Business Systems — it may indicate a Python or credential issue on the server side.

**The Customer 360 view shows no invoices for an account I know has open items.**
This could be a timing issue (the customer detail is queried live from NetSuite). Wait a moment and click the account again. If the problem persists, contact Business Systems.

**Can I use the dashboard on my phone or tablet?**
The dashboard is designed for desktop use. It can be accessed from a tablet browser but the layout is optimized for a full-width screen.

**Who do I contact for help?**
Contact the Business Systems team. For urgent data issues (balances appear completely wrong, dashboard not loading), reach out to Zach Bergman or the intern/IT contact who manages the Azure deployment.

---

_Last updated: 2026-07-27_
_Built by Zach Bergman (Business Systems intern, Summer 2026)_
_For Finance Operations and Collections leadership_
