# AR Dashboard + Pulse Deck — Where We Left Off (2026-06-04)

Quick-start notes so you can pick up tomorrow.

## ▶ To start tomorrow
1. Double-click **`launch.bat`** in `C:\Users\ZachBergman\ar-dashboard`
   (or run `npm run dev` in that folder). It starts the backend + frontend.
2. Open **http://localhost:5173** (or http://localhost:3001).
3. If you just want to re-open Claude Code to keep building: open it in
   `C:\Users\ZachBergman` — my memory loads automatically with all this context.

## ✅ What's working (live)
- **Dashboard is LIVE on NetSuite sandbox.** Header button **"⟳ Pull live from NetSuite"**
  re-pulls fresh data (~10s) → updates every tile, Top-10, etc.
- **NetSuite is the source of truth** — overdue balances, aging, DPD buckets, reps,
  cash, customers all come live from NetSuite via SuiteQL.
- **"⬇ Generate Pulse Deck"** button → builds Jordan's AR Executive Pulse deck with
  current data + 8 charts in her format (cash charts, payment methods, aging strip),
  with anything not-yet-sourced clearly marked `[update]` / placeholder.
- UI flicker bug fixed.

## 🎞 Pulse Deck — CFO polish pass (2026-06-05)
Made the generated deck cleaner/more professional. All live (restart of `npm run dev`
done so the button picks up the pulseData.js change). To eyeball results: render the
deck to PNGs via PowerPoint COM (script pattern in session history) → `_review/` folder.
- **Full numbers everywhere** — `charts.py` (`_abbr`/`_money`/axis) and `pulse/pulseData.js`
  (`fmtUSD`) now emit `$1,234,567`, never `$1.2M`. Tables + charts consistent.
- **Softened placeholders** — `BLANK = "—"` (was `[update]`); `render_placeholder` is now a
  quiet light-gray panel ("awaiting <src> data"), not a dashed draft box.
- **AR Tracker scalars** — `ar_tracker.read_scalar_tokens()` fills CASH_MTD, CASH_MTD_PCT,
  AGING60_TARGET from the monthly/Daily-Cash tabs (override in build_pulse.py, AR Tracker =
  official cash source). Only unambiguous, clearly-labeled cells — QTD/DSO left soft.
- **Chart restyle** — navy titles, Calibri font (matches deck), subtle gridlines on tva.
- **Template fixes** — slide-2 "Decisions / Updates" spacing + nbsp; **tokenized the stale
  hardcoded `37` (DSO) and `Medium` (Forecast) cells** → now `{{DSO}}`/`{{FORECAST_CONFIDENCE}}`.
  Template backed up at `pulse-deck-agent/pulse_template.backup.pptx`.
- **KNOWN STALE (not yet fixed):** slide 9 "May '26 / Q2 '26" weekly scoreboard tables are
  embedded images from ~5/21 (data stops mid-May) — need AR Tracker weekly-scoreboard image
  generation. Also static narrative (Risks/Decisions bullets, slide-3 annotations,
  "(Ahead of Q2 target)") = Jordan edits weekly. Aging trend charts still YayPay placeholders.

## ⚠️ Notes
- **Sandbox data ≠ production.** Sandbox shows ~$35M overdue and **$0 cash** (no recent
  test payments). For the real Friday deck, swap to production in `.env`:
  `NS_ACCOUNT_ID=8151367` (drop `_SB1`) + **production** TBA tokens. Same code.
- **🔒 Rotate the NetSuite access token** in NetSuite when done testing (it was shared in chat).
- **Salesforce live = ✅ WORKING (2026-06-05).** Solved the admin-toggle blocker by
  switching from client-credentials to the **authorization-code flow** (you log in as
  yourself in the browser — no SF admin needed). Live pull returns 11,604 SF accounts.
  - One-time login: `python sf_auth.py` (opens browser → PKCE → saves `SF_REFRESH_TOKEN`
    to `.env`). Re-run only if the refresh token is ever revoked/expires.
  - `sf_client.py` now uses `SF_REFRESH_TOKEN` automatically; falls back to
    client-credentials if no refresh token is present.
  - Connected-app callback URL must stay `http://localhost:3001/auth/callback`.

## 🔑 Credentials
All in `ar-dashboard/.env` (git-ignored). NetSuite TBA tokens + account `8151367_SB1`;
Salesforce client id/secret + `advantive--full` sandbox URLs.

## 🗂 Key files
**ar-dashboard/**
- `server.js` — backend (APIs: `/api/dashboard`, `/api/refresh`, `/api/pulse-deck`)
- `live_snapshot.py` — pulls live NS (+ SF fallback) → writes `hybrid-snapshot.json`
- `ns_client.py` — NetSuite SuiteQL client (TBA)  ·  `sf_client.py` — Salesforce SOQL client (ready, pending SF toggle)
- `pulse/pulseData.js` — maps snapshot → pulse-deck data
- `src/App.jsx` — dashboard UI

**pulse-deck-agent/** (the deck builder, called by the dashboard)
- `build_pulse.py` — fills `pulse_template.pptx` (Jordan's deck) with data + charts
- `charts.py` — matplotlib chart generators (Jordan's format)
- `ar_tracker.py` — reads the AR Tracker workbook for cash charts
- AR Tracker source file: `C:\Users\ZachBergman\Downloads\2026 Advantive AR Tracker (1).xlsx`
  (drop the fresh weekly download there; configurable via env `PULSE_AR_TRACKER`)

## 📋 Open items (next sessions)
1. Forward the SF admin note → get Salesforce live (1 toggle, no code change).
2. When ready for the real deck: production NetSuite creds in `.env`.
3. Charts still manual/placeholder: >60/>90 trend (needs weekly snapshot archiving —
   could set that up), root cause (no data source), Integrated-vs-Non-Integrated (slide 9).
4. Tokenize the narrative text (Decisions/Risks) so nothing carries over.
5. Demand Letter Agent config is backed up at GitHub: `Advantive-Business-Systems/demand-letter-agent`.
