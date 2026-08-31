# Back Pocket Blue Deck Builder

ChatGPT/Claude project that automates Laura Day's quarterly "Back Pocket Blue" board-backup deck (US-04772). Given two Excel input files and live Salesforce pipeline data, it builds the 4-slide PPTX with no manual deck-building steps beyond providing inputs.

## What it is

Back Pocket Blue is the backup schedule Phil uses to answer board questions after the main board deck is finalized. It is a 4-slide PPTX:

1. **Title slide** — "Advantive [Month] Board Call", meeting date, "BACK POCKET BLUE"
2. **Pipeline Coverage** — open pipeline vs. budget/forecast by LOB and product (Q3 & Q4)
3. **Capacity Breakdown** — quota, bookings, headcount, productivity, and attainment by LOB
4. **Bookings Bridge** — actuals and forecast vs. BOD forecast, with variance, by LOB

## How it's built

This is a **Claude.ai Project** (not a local script). The project instructions act as the system prompt, and Claude handles all data processing and deck generation when Laura provides inputs in a chat.

**Claude.ai Project:** Back Pocket Blue Deck Builder (private, Laura Day's workspace)

### Files in the project
- `project_instructions.md` — system prompt / operating instructions pasted into the claude.ai project's Instructions field
- `generate_mock_inputs.py` — generates realistic test versions of both Excel input files (matching exact column structure of the real files)

### Files uploaded to the claude.ai project
- `BackPocketBlue_Handoff_Instructions.docx` — full engineering spec (Laura Day's SharePoint)
- `2026.04.21 Advantive FY26Q1 Board Meeting -Back Pocket Blue.pptx` (as PDF) — reference deck

## Inputs required each cycle

| Input | Source |
|-------|--------|
| `Bookings_Input_MMDDYY.xlsx` | Brandon Bussey's SharePoint → `01_Transition/1_ForecastBoardReporting/BackPocketBlue Update` |
| `Capacity_Input_MMDDYY.xlsx` | Same folder |
| Board meeting date | Laura confirms each cycle |
| Current quarter | Laura confirms each cycle |
| Q2→Q3 push rate | Default 35% — confirm with Phil each cycle |

## Salesforce data

The claude.ai project has the Advantive Salesforce MCP connector attached. Claude runs the SOQL pipeline query directly (Q2, Q3, Q4 pulls) — Laura does not need to export anything manually.

## Key technical rules

- **Always python-pptx for tables** — never PptxGenJS (LibreOffice ignores PptxGenJS column widths)
- **Services Bookings** must filter `Revenue Type == 'Services'` on ACV Bookings — missing this filter causes 2–3x inflation
- **FY26 Capacity HC** = average of 4 quarterly values, never a sum
- Brand palette: Plum Deep `#3B2845`, Orange `#F58220`, Plum Ink `#5A3F6B`, Carbon `#353A45`
- Font: Aptos (Calibri fallback)

## Source files (SharePoint)

- Handoff doc: Laura Day's OneDrive → `Documents/Attachments/BackPocketBlue_Handoff_Instructions.docx`
- Reference deck: Laura Day's OneDrive → `Documents/Attachments/2026.04.21 Advantive FY26Q1 Board Meeting -Back Pocket Blue.pptx`
- Input workbooks: Brandon Bussey's OneDrive → `01_Transition/1_ForecastBoardReporting/BackPocketBlue Update/`

## Stakeholders

- **Owner:** Laura Day
- **Story:** US-04772 (Epic: Corporate AI Work)
- **Owner (story):** Jordan Vasquez
- **Built by:** Zach Bergman (intern, July 2026)
