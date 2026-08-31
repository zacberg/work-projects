# Back Pocket Blue Deck Builder — Technical Documentation

**Last updated:** 2026-07-27
**Built by:** Zach Bergman (Business Systems intern, July 2026)
**Story:** US-04772 (Epic: Corporate AI Work) — Owner: Jordan Vasquez
**Status:** Built; see project_instructions.md for the system prompt

---

## Overview

The Back Pocket Blue Deck Builder automates the quarterly "Back Pocket Blue" board-backup deck that Phil uses to answer board questions after the main board deck is finalized. It is a Claude.ai Project — not a local script or a deployed service. Laura Day uploads two Excel input files to a Claude.ai chat; Claude pulls live Salesforce pipeline data via MCP, processes all inputs, and produces a download-ready 4-slide PPTX.

---

## Output

A 4-slide PPTX named for the board call date:

| Slide | Title | Content |
|-------|-------|---------|
| 1 | Title | "Advantive [Month] Board Call", board meeting date, "BACK POCKET BLUE" |
| 2 | Pipeline Coverage | Open pipeline vs. budget/forecast by LOB and product, Q3 and Q4 |
| 3 | Capacity Breakdown | Quota, bookings, headcount, productivity, and attainment by LOB |
| 4 | Bookings Bridge | Actuals and forecast vs. May BOD forecast, with variance, by LOB |

---

## Architecture

| Component | Detail |
|-----------|--------|
| Platform | Claude.ai Project (private; Laura Day's workspace) |
| Model | Claude (latest available in claude.ai Projects) |
| Salesforce data | Pulled directly via Advantive Salesforce MCP connector attached to the project |
| Excel processing | Python (pandas) executed in Claude's code environment |
| PPTX generation | python-pptx — always; never PptxGenJS (LibreOffice ignores PptxGenJS column widths) |
| Deployment | None — runs entirely within claude.ai; no server or local script |

---

## Project Files

### In the repo (C:\Users\ZachBergman\_docs-work\back-pocket-blue-deck-builder\)

| File | Purpose |
|------|---------|
| `project_instructions.md` | System prompt pasted into the claude.ai Project's Instructions field |
| `generate_mock_inputs.py` | Generates realistic test versions of both Excel inputs for development/testing |
| `README.md` | Project overview and stakeholder notes |

### Uploaded to the claude.ai Project (not in repo)

| File | Source | Purpose |
|------|--------|---------|
| `BackPocketBlue_Handoff_Instructions.docx` | Laura Day's OneDrive → Documents/Attachments/ | Full engineering specification |
| `2026.04.21 Advantive FY26Q1 Board Meeting -Back Pocket Blue.pptx` (as PDF) | Laura Day's OneDrive → Documents/Attachments/ | Reference deck for structural validation |

---

## Inputs Required Each Cycle

| Input | Source | Notes |
|-------|--------|-------|
| `Bookings_Input_MMDDYY.xlsx` | Brandon Bussey's OneDrive → `01_Transition/1_ForecastBoardReporting/BackPocketBlue Update/` | Must be current month's file |
| `Capacity_Input_MMDDYY.xlsx` | Same folder | Must be current month's file |
| Board meeting date | Laura confirms each cycle | Used on title slide and slide headers |
| Current quarter | Laura confirms each cycle | Determines Actuals vs. Forecast column labels |
| Q2→Q3 push rate | Default 35% — confirm with Phil each cycle | Applied to Q3 Pipeline Coverage calculation |

---

## Salesforce Pipeline Query

Claude runs the following SOQL query three times (once each for Q2, Q3, and Q4). If the MCP connector is unavailable, Laura can run the query manually and re-upload the result as CSV.

```sql
SELECT Id, Primary_PH06_Product__c, Business_Unit__c, Product_Brands__c, Total_eACV__c
FROM Opportunity
WHERE RecordType.Name IN ('Sales', 'Amendment')
AND Subtype__c NOT IN ('Migration','Decommission','Renewal','Debooking','Partial Decommission','Full Decommission','Rebooking')
AND Total_eACV__c > 0
AND StageName NOT IN ('Closed Won','Closed Lost')
AND CloseDate >= [QUARTER_START]
AND CloseDate <= [QUARTER_END]
ORDER BY Id LIMIT 200
```

**FY26 quarter date ranges:**

| Quarter | Start | End |
|---------|-------|-----|
| Q2 | 2026-04-01 | 2026-06-30 |
| Q3 | 2026-07-01 | 2026-09-30 |
| Q4 | 2026-10-01 | 2026-12-31 |

**Important:** Do not filter `Opportunity_Owner_Role_formula__c` inside SOQL. Pull row-level data and filter CSM / Data Migration roles in post-processing.

---

## Product → LOB → Brand Mapping

Three-tier fallback:

**Tier 1: Product name**

| Product | LOB | Brand |
|---------|-----|-------|
| Inform | Distribution | DDI |
| ERP-ONE | Distribution | DS1 |
| Opening Suite | Distribution | COM |
| CVe, Lucy, Opmetrix | Distribution | CVO |
| Pepperi | Distribution | PEP |
| Kiwiplan | Packaging | KWP |
| Packaging 3000 | Packaging | ABS |
| Enact, ProFicient, ProFicient On Demand | Quality | IQS |
| GAGEpack | Quality | PQS |
| SQCpack | Quality | PQS |
| Proplanner | Manufacturing | PRO |
| SmartScreen | Manufacturing | PIN |
| Plant Manager | CFP | PFC |
| WinSPC | CFP | DQS |
| MAN-IT | CFP | VIA |
| VeraCore | CFP | VER |
| Advantzware | CFP | ADW |

**Tier 2: Business Unit fallback (when product is null)** — see `project_instructions.md` for full mapping.

**Tier 3:** When both product and BU are null, surface for manual assignment.

**IQS null-split rule:** Any null-product opportunity mapping to IQS gets allocated 1/3 each to Enact, ProFicient, and ProFicient On Demand (applies to both pipeline and budget/forecast numbers).

---

## Excel Input File Schema

### Bookings_Input (sheet: Bookings.Detail)

Key columns: Source, Year, Quarter, LOB, Product, Measure, Revenue Type, Value.

| Source value | Used for |
|-------------|---------|
| Current | Q1 actuals + Q2/Q3/Q4 current forecast (all three data slides) |
| May BOD Forecast | Prior board forecast (Bookings Bridge slide only) |
| Budget | Annual budget targets (Pipeline Coverage slide) |

| Measure value | Used for |
|--------------|---------|
| LEB SW Bookings | Primary bookings metric — all slides |
| ACV Bookings (Revenue Type == 'Services' only) | Services Bookings rows on Bookings Bridge |

**Critical:** Services Bookings must filter `Revenue Type == 'Services'` on ACV Bookings. Missing this filter produces numbers 2–3x too high.

### Capacity_Input

Header row is row 3 (index 2 in pandas).

Left-side columns: PH04, PH05, PH06, Quarter, Month, Effective HC, Quota, ExpBookings.

PH04 → LOB mapping: PACK = Packaging, DIST = Distribution, MANF = Manufacturing, QUAL = Quality, CFP = Customer Focused Products.

| Metric | Formula |
|--------|---------|
| Effective Quota Outstanding | SUM(Quota) / 1000 → $M |
| LEB Software Bookings | From Bookings_Input, Current source, by LOB + quarter |
| Effective Quota Carrying Headcount | SUM(Effective HC) / 3 (monthly average — never a sum) |
| Effective Rep Productivity | Sum of above three metrics |
| Attainment % | LEB SW Bookings / Effective Quota Outstanding |
| FY26 HC | Average of 4 quarterly HC values — NEVER sum |

---

## PPTX Construction Rules

| Rule | Detail |
|------|--------|
| Library | python-pptx only; never PptxGenJS |
| Slide size | 13.33" × 7.5" (widescreen) |
| Font | Aptos; Calibri as fallback |
| Column/row sizing | Set explicitly on both table object and every cell — no auto-sizing |
| Number format (dollars) | $X.XM (one decimal) |
| Number format (coverage) | X.Xx |
| Number format (capacity metrics) | One decimal (e.g. 13.4); Attainment as whole percent (e.g. 83%) |

### Brand Color Palette

| Name | Hex | Used for |
|------|-----|---------|
| Plum Deep | #3B2845 | Title bars, section headers, subtotal rows, LOB total rows |
| Orange | #F58220 | Grand total rows |
| Plum Ink | #5A3F6B | Section group headers, subtotal borders |
| Carbon | #353A45 | Subtitle text, Q4 section header |
| Light Gray | #F0F0F0 | LOB name rows (section break) |
| White | #FFFFFF | Data rows |
| Green | #D6EFCE | Positive variance fill |
| Amber | #FFF2CC | Coverage 1.0x–1.9x |
| Red | #FFDCE0 | Negative variance fill / coverage under 1.0x |
| Red Text | #C00000 | Negative variance text |

Coverage heat map thresholds: ≥2.0x = green · 1.0x–1.9x = amber · <1.0x = red.

---

## How to Configure / Update the Project

The system prompt lives in `project_instructions.md`. To update the claude.ai Project:

1. Edit `project_instructions.md` in this repo and commit.
2. Open the claude.ai Project → **Project Settings** → **Instructions**.
3. Replace the existing text with the updated content from `project_instructions.md`.
4. If the engineering spec or reference deck changes, upload the updated versions to the Project's file library.

---

## Pre-Send Checklist (each build cycle)

- [ ] Salesforce pipeline pulled fresh for Q2, Q3, and Q4
- [ ] No unassigned null product/BU rows remain
- [ ] Services Bookings filtered to `Revenue Type == 'Services'`
- [ ] Forecast columns use Current source (not May BOD Forecast)
- [ ] Budget columns use Budget source
- [ ] Coverage heat map thresholds correct (≥2.0x green · 1.0–1.9x amber · <1.0x red)
- [ ] FY26 capacity HC is an average of 4 quarters, not a sum
- [ ] All dollar amounts in $M with one decimal
- [ ] Title slide has the correct board meeting date
- [ ] python-pptx used throughout — not PptxGenJS
- [ ] Latest Bookings_Input and Capacity_Input files confirmed (current month)

---

## Known Edge Cases

| Symptom | Explanation |
|---------|-------------|
| Manufacturing Q3 Services jumps sharply | Expected — large SmartScreen/PINpoint services deal moving quarters; not an error |
| IQS products show wrong budget | Budget at PH06 uses product codes (ENA/POD/POP), not display names like "Enact" |
| Capacity Attainment over 100% | Normal when actuals exceed quota — not an error |
| Table columns render equal-width in LibreOffice | File was built with PptxGenJS — rebuild the affected slides with python-pptx |

---

## Stakeholders

| Role | Person |
|------|--------|
| Owner / primary user | Laura Day |
| Board presenter | Phil |
| Story owner | Jordan Vasquez |
| Input file source | Brandon Bussey |
| Builder | Zach Bergman (intern) |
