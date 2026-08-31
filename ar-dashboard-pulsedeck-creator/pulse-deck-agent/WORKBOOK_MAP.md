# AR Tracker workbook — structural map (2026 Advantive AR Tracker.xlsx)

Source of truth confirmed. 26 sheets, 54 native Excel charts. Mapped 2026-06-03.

## Key tabs
- **Weekly Deck Slide - RunRates** ← dedicated deck-staging tab (8 charts feed the Pulse deck)
- **Daily Cash Email Send** ← source of the daily/weekly cash update email
- **Monthly Totals** (12 "X Cash: Target VS Actual" charts), **Quarterly Totals** (13 cash-vs-target / run-rate charts), **Yearly Totals**
- Monthly tabs `January 2026 … Dec 2026` (each has one "AR Collection Tracker" daily-cash bar chart)
- `X Payments & Aging` tabs — raw aging/invoice data, ~17k-row tables (A2:R), **no charts on them**

## Deck CASH charts — all native Excel, exportable identical (THIS workbook)
| Deck slide | Chart | Workbook chart | Tab |
|---|---|---|---|
| 3 | Weekly Cash Run Rate: Avg | chart3 | Weekly Deck Slide - RunRates |
| 3/9 | Quarterly Avg Run Rate / Totals | chart4, chart5 | Weekly Deck Slide - RunRates |
| 3 | Q1'26 Cash vs Target | chart2 | Weekly Deck Slide - RunRates |
| 9 | Total Cash Collected '24-'26 (pie) | chart7 | Weekly Deck Slide - RunRates |
| 9 | Payment Methods (pie, "Count of Date") | chart8 | Weekly Deck Slide - RunRates (R111:S115) |
| 9 | Integrated vs Non-Integrated | chart6 | Weekly Deck Slide - RunRates |
| 2/9 | May Cash: Target VS Actual | chart15 | Monthly Totals |
| — | Q2'26 Cash vs Target | chart34 | Quarterly Totals |

## Deck AGING / RISK charts — NOT in this workbook (built elsewhere on this data)
Deck slides 4, 5, 7, 10, 11 visuals are **missing** from this file's chart list:
- >60 Trend, >90 Trend, Total AR aging strip, Payments Against >60, Payments by Timing %/$,
  Root Cause (5-series), Upcoming to >60 (donut).
- Their underlying DATA lives here (the `Payments & Aging` tabs, ~17k rows), but the CHARTS
  are built somewhere else on that data — their styling matches **Power BI**.

## Implication for the build
- **Cash half of the deck** → fully solvable from this workbook now: read cells for numbers,
  export the native Excel charts as images (identical). No Power BI.
- **Aging half** → need to confirm the source:
  - If **Power BI** (likely, by look) → identical export needs Power BI access for that half,
    OR regenerate from the `Payments & Aging` data already in this file (close, not identical).
  - If **another Excel file** → all-Excel, same clean path.

## OPEN QUESTION FOR USER / JORDAN
Where do the aging charts (>60 Trend, Payments by Timing, Root Cause, Upcoming to >60, etc.)
come from — a Power BI report, or another Excel file? The data is in this workbook's
`Payments & Aging` tabs, but the charts are not. This is the last unknown for the build.
