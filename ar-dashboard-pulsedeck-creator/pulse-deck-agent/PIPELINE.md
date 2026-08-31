# AR Executive Pulse — automation pipeline (current state)

**Goal:** auto-produce as much of Jordan Duke's weekly Friday "AR Executive Pulse"
deck as possible. ChatGPT agent triggers it; a builder service fills a fixed
template so the deck is layout-identical every week.

## Architecture (decided 2026-06-04)

```
ChatGPT agent  ──webhook──>  n8n Cloud
                                │  1. read cash numbers from AR Tracker (Graph usedRange)
                                │  2. fetch 5 cash chart images (Graph workbook chart-image API)
                                │  3. assemble pulse_data JSON (agent drafts narrative)
                                ▼
                         Builder service  (POST /build)   ← external; n8n Cloud can't run python-pptx
                                │  fills pulse_template.pptx: tokens + Top-10 table + cash chart swaps
                                ▼
                         finished .pptx  ──> download link back to the agent
```

## What's automated vs manual

| Part | Source | Status |
|---|---|---|
| All slide text + metric numbers (cash MTD/QTD, attainment, run-rate, holds, scoreboard, top-movers) | AR Tracker workbook / agent | ✅ automated (tokens) |
| Top-10 past-due table (exposures + drafted notes) | AR Tracker + agent narrative | ✅ automated (tbl_top10) |
| 5 **cash** charts (weekly run rate, cash vs target ×2, payment methods) | AR Tracker **native Excel charts** via Graph image API | ✅ automated (image swap) |
| 8 **aging** charts (>60/>90 trend, root cause, total AR aging, upcoming-to-60, payments-against-60, payments-by-timing %/$) | **YayPay / Power BI** — NOT in the workbook | ⛔ manual snip for now (see below) |
| Aging metrics (>60/>90 balances, movement) | YayPay | ✍️ agent enters values into JSON |
| Narrative (decisions, risks, root-cause text, per-customer notes) | agent draft, Jordan reviews | ✍️ drafted, human-reviewed |

### Why the 8 aging charts are manual
Validated 2026-06-04: the aging buckets/trends/root-cause data are **not** in the
AR Tracker. Naive regeneration from the raw `Payments & Aging` rows does not
reconcile (computed >60 = $0.5M vs actual $2.8M) because aging uses YayPay
business logic + formula fields that don't evaluate in a static copy, and
root-cause/trend series don't exist in the file at all. Faithful automation needs
**YayPay or Power BI access** (not currently available). Until then those 8 chart
shapes are left as last week's image and re-snipped by hand. The builder enforces
this automatically: any chart shape NOT supplied an image is left untouched.

## Files
- `pulse_template.pptx` — the fixed, tokenized template (5 named tables, 13 named chart shapes). **Don't edit layout.**
- `build_pulse.py` — the builder (tokens, Top-10 table, cash chart image swap). Used both locally and by the service.
- `pulse_data.example.json` — the weekly input schema the agent fills.
- `service/app.py` — FastAPI wrapper (`POST /build`, `GET /health`) that n8n calls.
- `service/requirements.txt`, `Dockerfile` — to host the service.
- `fix_template.py`, `make_template.py`, `name_charts.py` — one-time template prep (already run).

## Run locally
```
python build_pulse.py pulse_data.json --charts-dir _charts
```

## Run the service
```
cd service && python -m uvicorn app:app --host 0.0.0.0 --port 8000
# POST /build  (multipart): data=<json string>, charts=<files named chart_<shape>.png>
```

## Open items
1. **Host the builder service** so n8n Cloud can reach it (deploy vs local+tunnel).
2. **n8n OAuth credential** — create the Microsoft Excel/Graph OAuth2 credential in n8n Cloud (currently `REPLACE_ME` in the Gather workflows).
3. **Aging charts** — get YayPay or Power BI access to fully automate the 8 aging charts + aging metrics.
4. Slide 5 "Top 4 likely to roll" + slide 2 ">90 note" + root-cause text on slide 7 are not yet tokenized — agent edits or we add tokens later.
