# AR Executive Pulse — Agent Setup

Automates Jordan Duke's weekly AR Executive Pulse deck. The agent gathers the week's
data via connectors, drafts the narrative, and runs `build_pulse.py` to fill a fixed
template — so the deck is pixel-identical every week and ready Friday.

## 1. Apps to connect in ChatGPT

| Connector | Why | Priority |
|---|---|---|
| **Microsoft SharePoint / OneDrive** | The AR Tracker workbook (aging, top-10, collection notes, cash, payment-timing) lives in the collections SharePoint. This is the main data source. | **Required** |
| **Salesforce** | Holds (under threat / on hold / hold-related payments) and any SF-sourced flags. | Recommended |
| **NetSuite** | AR balances, DSO, collections this week — *if* a NetSuite connector exists. If not, this data can come from the AR Tracker or the AR dashboard's snapshot. | If available |

Also enable, in the GPT's **Capabilities**: **Code Interpreter & Data Analysis**
(required — it runs `build_pulse.py` + matplotlib).

## 2. Knowledge files to upload to the GPT
- `pulse_template.pptx`  ← the tokenized template (make once — see step 3)
- `build_pulse.py`       ← the generator (don't let the model edit it)
- `pulse_data.example.json` ← the data schema the agent fills each week

## 3. One-time: make the tokenized template
Open Jordan's deck (`AR Executive Pulse Week Ending 5.21.26.pptx`) in PowerPoint and
replace each *dynamic* value with its token, then **Save As `pulse_template.pptx`**.
Static things (title art, layout, labels) stay as-is. Token map:

| In the deck (slide) | Replace with token |
|---|---|
| Title "Week Ending 5/21/26" (s1) | `{{WEEK_ENDING_LABEL}}` |
| Cash (MTD) "$8.8M" / "72%" (s2) | `{{CASH_MTD}}` / `{{CASH_MTD_PCT}}` |
| Cash (QTD) "$26.2M" / "58%" (s2) | `{{CASH_QTD}}` / `{{CASH_QTD_PCT}}` |
| DSO "37" (s2) | `{{DSO}}` |
| >60 Balance "$2.84M" / collections "$292k" (s2) | `{{BAL_60}}` / `{{COLL_60_WEEK}}` |
| >90 Balance "$1.40M" + note / collections "$297k" (s2) | `{{BAL_90}}` / `{{BAL_90_NOTE}}` / `{{COLL_90_WEEK}}` |
| Forecast confidence "Medium" (s2) | `{{FORECAST_CONFIDENCE}}` |
| Decisions/Updates + Risks (s2) | `{{DECISIONS_UPDATES}}` / `{{RISKS_TO_CASH}}` |
| >60 aging movement block (s4) | `{{AGING60_START}}` `{{AGING60_ROLLED_IN}}` `{{AGING60_COLLECTED}}` `{{AGING60_ENDING}}` `{{AGING60_TARGET}}` `{{AGING60_MOVEMENT}}` |
| >90 aging movement block (s10) | `{{AGING90_START}}` `{{AGING90_ROLLED_IN}}` `{{AGING90_COLLECTED}}` `{{AGING90_WRITEOFFS}}` `{{AGING90_ENDING}}` `{{AGING90_TARGET}}` `{{AGING90_MOVEMENT}}` |
| Scoreboard highlights (s9) | `{{SCORE_MAY_DAILY_AVG}}` `{{SCORE_MAY_ATTAINMENT}}` `{{SCORE_Q2_ATTAINMENT}}` `{{TOP_MOVER_1..3}}` |
| Holds (s11) | `{{HOLDS_UNDER_THREAT}}` `{{HOLDS_ON_HOLD}}` `{{HOLDS_RELATED_PAYMENTS}}` |
| Root causes (s7) | `{{ROOT_CAUSE_1..3}}` `{{ROOT_CAUSE_CHANGED}}` `{{ROOT_CAUSE_ASK}}` |

Then, in PowerPoint's **Selection Pane**, name the shapes the script targets:
- Top-10 customer table (s6) → name it `tbl_top10`
- Top-4 likely-to-roll table (s5) → name it `tbl_top4_roll`
- "Payments by Timing %" chart picture (s9) → name it `chart_payments_timing`

(That's how `build_pulse.py` finds them. Add more chart names as you wire up more charts.)

## 4. Weekly run
The agent (or you) assembles `pulse_data.json` from the connectors, then runs
`python build_pulse.py pulse_data.json` → out comes the finished deck.

## Notes / honest scope
- **Charts:** `build_pulse.py` fully regenerates the "Payments by Timing" chart as the
  working pattern. The other ~7 charts are stubbed — each needs its data series + a
  `chart_*` function (copy the pattern) and a named picture in the template. Wire them
  in one at a time.
- **Narrative is a draft.** The agent drafts root-cause / next-action text from the AR
  Tracker notes; Jordan reviews before sending. Don't auto-send.
- **Cash-update dependency:** the deck can't be finalized until the weekly cash update
  is received (it's event-driven, not scheduled). The GPT instructions enforce this.
