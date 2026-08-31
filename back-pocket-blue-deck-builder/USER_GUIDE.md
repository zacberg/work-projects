# Back Pocket Blue Deck Builder — User Guide

**Audience:** Laura Day
**Last updated:** 2026-07-27

---

## What It Does

The Back Pocket Blue Deck Builder builds the quarterly board-backup PPTX automatically. You provide two Excel files and confirm a few parameters; Claude pulls the Salesforce pipeline data, processes everything, and returns a finished 4-slide PPTX ready for Phil's board call.

No manual deck-building, no chart copy-pasting, no number lookups.

---

## Where to Access It

**claude.ai** → open the **Back Pocket Blue Deck Builder** Project

If you do not see it, ask Business Systems (Zach Bergman / Jordan Vasquez) to share it with your account.

---

## What You Need Before Starting

### From Brandon Bussey's SharePoint folder:
`Brandon Bussey / OneDrive / 01_Transition / 1_ForecastBoardReporting / BackPocketBlue Update /`

- `Bookings_Input_MMDDYY.xlsx` — current month's version
- `Capacity_Input_MMDDYY.xlsx` — current month's version

**Always use the current month's files.** Do not reuse a prior cycle's files.

### Confirmed from Phil or the calendar:
- Board meeting date (used on the title slide and slide headers)
- Current quarter (e.g., Q3)
- Q2→Q3 push rate (default: 35% — confirm with Phil each cycle)

---

## How to Build the Deck

### Step 1 — Start a new chat in the Project

Open the Back Pocket Blue Deck Builder Project on claude.ai and start a new conversation.

### Step 2 — Confirm the parameters when Claude asks

Claude will ask you to confirm:
- Board meeting date
- Current quarter
- Fiscal year (default: FY26)
- Q2→Q3 push rate (default: 35%)

Reply with your confirmed values.

### Step 3 — Upload the two Excel files

Upload `Bookings_Input_MMDDYY.xlsx` and `Capacity_Input_MMDDYY.xlsx` from SharePoint. You can attach both in the same message.

### Step 4 — Wait for Claude to pull Salesforce data

Claude pulls the open pipeline from Salesforce directly (Q2, Q3, and Q4 pulls). You do not need to export anything from Salesforce manually. This may take a minute.

If the Salesforce connector is unavailable, Claude will provide a SOQL query for you to run manually and re-upload as a CSV.

### Step 5 — Download the finished PPTX

Claude returns a download-ready PPTX file. Download it and open it in PowerPoint or your preferred presentation app.

---

## What the Deck Contains

| Slide | Content |
|-------|---------|
| 1 — Title | "Advantive [Month] Board Call", board meeting date, "BACK POCKET BLUE" |
| 2 — Pipeline Coverage | Open pipeline vs. budget and forecast by LOB and product for Q3 and Q4 |
| 3 — Capacity Breakdown | Quota, bookings, headcount, productivity, and attainment by LOB |
| 4 — Bookings Bridge | Actuals and forecast vs. prior BOD forecast, with variance by LOB |

---

## Common Issues

| Symptom | What to do |
|---------|-----------|
| Claude uses an old cycle's numbers | Confirm you uploaded the current month's Excel files, not a prior version |
| Push rate seems wrong in the deck | Reply to Claude in the same chat specifying the correct push rate; Claude will regenerate the affected slide |
| Salesforce MCP is unavailable | Claude will give you a SOQL query; run it in Salesforce, export as CSV, and upload the CSV to the chat |
| Numbers look significantly off on one slide | Check the specific LOB or product; reply to Claude describing what looks wrong and it will investigate and correct |
| PPTX column widths are uneven in LibreOffice | Open in PowerPoint instead — the file is built for PowerPoint; LibreOffice can render column widths differently |
| Claude asks which Advantive entity | This should not happen for standard builds (default is Advantive LLC). If it does, reply "Advantive LLC" |

---

## Cycle Checklist

Before handing the deck to Phil, verify:

- [ ] Title slide shows the correct board meeting date
- [ ] Current quarter is labeled correctly (Actuals vs. Forecast columns match)
- [ ] Push rate confirmed with Phil
- [ ] Pipeline numbers are from fresh Salesforce data (this cycle, not last cycle)
- [ ] Bookings Bridge variance columns are color-coded (green = favorable, red = unfavorable)
- [ ] No "#" or error values in any cell

---

## Key People

| Person | Role |
|--------|------|
| Laura Day | Owner — runs the deck each quarter |
| Phil | Board presenter — reviews and uses the deck |
| Jordan Vasquez | Story owner (US-04772) |
| Brandon Bussey | Source of the Excel input files (SharePoint) |
| Zach Bergman | Builder — contact for technical issues |
