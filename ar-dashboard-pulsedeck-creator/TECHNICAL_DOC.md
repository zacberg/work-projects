# AR Dashboard + Pulse Deck Creator — Technical Documentation

**Project:** AR Collections Dashboard and Weekly Pulse Deck Generator
**Owner:** Business Systems (Zach Bergman, 2026 summer intern)
**Primary users:** Jordan Duke (Finance Operations), Justin Wixom
**Status:** Live on Azure. In active use for daily AR monitoring and weekly executive reporting.

---

## Table of Contents

1. [Maintenance and Support](#1-maintenance-and-support)
2. [How the Dashboard Works](#2-how-the-dashboard-works)
3. [How to Configure and Deploy Updates](#3-how-to-configure-and-deploy-updates)
4. [Additional Technical Information](#4-additional-technical-information)

---

## 1. Maintenance and Support

### 1.1 Credential Rotation

All credentials are stored in the `.env` file on the Azure container (passed as App Settings in the Azure Web App). None are committed to the repository.

#### NetSuite — Token-Based Authentication (OAuth 1.0a)

NetSuite credentials consist of four values: consumer key/secret (tied to the Connected App) and token ID/secret (tied to the integration user). These do not expire on a fixed schedule but must be regenerated if the integration user is deactivated, the Connected App is rotated, or the token is manually revoked.

| Env variable | Description |
|---|---|
| `NS_ACCOUNT_ID` | NetSuite production account ID (`8151367`) |
| `NS_CONSUMER_KEY` | OAuth 1.0a consumer key |
| `NS_CONSUMER_SECRET` | OAuth 1.0a consumer secret |
| `NS_TOKEN_ID` | Token ID |
| `NS_TOKEN_SECRET` | Token secret |

To regenerate: in NetSuite, navigate to Setup > Integration > Manage Integrations, then regenerate the token for the integration user. Update all four values in Azure App Settings and restart the container.

#### Salesforce — OAuth 2.0 Refresh Token

Salesforce authentication uses an authorization-code flow. A refresh token is saved after a one-time browser login. Refresh tokens do not expire unless revoked, but they must be regenerated if the Connected App credentials change or the token is revoked in Salesforce.

| Env variable | Description |
|---|---|
| `SF_CLIENT_ID` | Connected App client ID |
| `SF_CLIENT_SECRET` | Connected App client secret |
| `SF_INSTANCE_URL` | `https://advantive.my.salesforce.com` (production) |
| `SF_REFRESH_TOKEN` | Long-lived refresh token (written by `sf_auth.py`) |

To regenerate the refresh token: run `python sf_auth.py` locally from the `ar-dashboard/` directory. This opens a browser, completes the PKCE authorization-code flow, and writes `SF_REFRESH_TOKEN` to `.env`. Copy the new value into the Azure App Settings and restart the container.

### 1.2 Common Issues and Diagnostics

| Symptom | Likely cause | Resolution |
|---|---|---|
| Dashboard shows stale data / "last updated" timestamp is old | Auto-refresh failed — usually an expired credential | Check Azure container logs for `[auto-refresh] skipped` errors; rotate the relevant credential |
| "Live refresh failed" error on manual pull | NetSuite or Salesforce auth error | Check container logs; look for `401` or `403` responses in the Python script output |
| Pulse Deck download fails | Python build error | Check container logs for `[pulse] build failed` and the `detail` field in the error response |
| Customer 360 shows no data | `customer_detail.py` failed | Check logs for `[live lookup failed]`; usually a NetSuite credential issue |
| Dashboard loads but shows zeros everywhere | Snapshot file is empty or corrupt | Manually trigger a refresh via the dashboard button; check container logs for the Python script stderr |
| "Could not run builder" on Pulse Deck | `PYTHON_BIN` misconfigured | Verify the Azure App Setting `PYTHON_BIN` points to the Python 3.11 executable inside the container |

### 1.3 Log Access

Container logs are available in the Azure Portal under the Web App > Monitoring > Log stream. The app writes `[refresh]`, `[auto-refresh]`, and `[pulse]` prefixed lines that identify the source of most errors.

### 1.4 Known Issues

- **Azure Deployment Center disconnected.** The GitHub↔Azure Deployment Center OIDC connection was broken when the GitHub repository was renamed. Pushing to `deploy/azure` does not currently trigger an automatic deploy. Manual deployment is required (see Section 3.2) until IT reconnects the Deployment Center.
- **Aging charts in the Pulse Deck are partially manual.** The 8 aging/risk charts (>60 trend, >90 trend, root cause, etc.) originate from YayPay/Power BI, which the build system does not have programmatic access to. Those chart shapes in the deck are carried forward from the previous week's images. Cash charts (5) are fully automated from the AR Tracker workbook.
- **AR Tracker dependency for Pulse Deck.** The Pulse Deck pulls scalar cash values (CASH_MTD, CASH_MTD_PCT, AGING60_TARGET) from the AR Tracker workbook. The path must be set in `PULSE_AR_TRACKER` in the environment, or the file must be placed at the expected path. If the weekly AR Tracker download is not available, those fields will appear as `—` placeholders in the deck.

---

## 2. How the Dashboard Works

### 2.1 Architecture Overview

The application is a single-container Node.js service. The Express backend serves the React frontend as static files and exposes API endpoints. Python 3.11 is spawned as a subprocess for all live data pulls and deck generation — it is not run as a separate server.

```
Browser
  └─ React 19 (Vite build, served as static files)
       └─ API calls → Express (server.js, port 3001)
                         ├─ /api/dashboard       → reads hybrid-snapshot.json
                         ├─ /api/refresh         → spawns live_snapshot.py
                         ├─ /api/customer        → spawns customer_detail.py
                         ├─ /api/pulse-deck      → spawns build_pulse.py
                         └─ /api/currencies      → fetch open.er-api.com (cached 1 hr)

live_snapshot.py
  ├─ ns_client.py  → NetSuite SuiteQL over OAuth 1.0a (HTTPS)
  └─ sf_client.py  → Salesforce SOQL via OAuth 2.0 refresh token
       └─ writes hybrid-snapshot.json

build_pulse.py (in pulse-deck-agent/)
  ├─ reads hybrid-snapshot.json (via pulse/pulseData.js mapping)
  ├─ reads AR Tracker workbook (ar_tracker.py → openpyxl)
  ├─ generates charts (charts.py → matplotlib)
  └─ fills pulse_template.pptx (python-pptx) → returns .pptx file
```

### 2.2 Data Flow

1. **Auto-refresh (server-side):** On startup, and every 5 minutes thereafter (configurable via `REFRESH_MINUTES`), the server spawns `live_snapshot.py`. This script runs SuiteQL queries against NetSuite production (account 8151367) and SOQL queries against Salesforce production, merges the results, and writes `hybrid-snapshot.json` to disk.

2. **Dashboard data:** The frontend polls `/api/dashboard` to read the snapshot. All tiles, tables, and charts in the dashboard are derived from this JSON file. The data is not streamed live — it reflects the most recent completed refresh.

3. **Manual refresh:** The user can trigger an immediate re-pull from the dashboard. This calls `POST /api/refresh`, which spawns `live_snapshot.py` and waits for it to complete (typically 10–20 seconds).

4. **Customer 360 drill-down:** This tab makes a real-time call to `/api/customer?entity=<id>`, which spawns `customer_detail.py` for that specific entity. It does not use the snapshot — it queries NetSuite and Salesforce live for the selected customer.

5. **Pulse Deck generation:** Triggered by `GET /api/pulse-deck`. The server reads the current snapshot, runs `pulseData.js` to map snapshot fields to deck tokens, then spawns `build_pulse.py` with the assembled data. The Python script fills the template and returns the `.pptx` file as a download.

6. **YayPay upload:** The frontend accepts a drag-and-drop CSV upload (summary or detailed format from YayPay). This data is processed client-side to reconcile YayPay balances against NetSuite balances visible in the Full Portfolio tab.

### 2.3 Dashboard Tabs

#### AR Overview
The landing tab. Shows the top-level portfolio health:
- Total open AR balance and total overdue balance
- 60+ DPD bucket balance (the primary collections focus metric)
- Accounts on support hold
- Placement queue (accounts flagged for external collections placement)
- Write-off pool
- Cash collected month-to-date

All figures are sourced from NetSuite (production). The 60+ DPD balance nets credit memos against open invoices to avoid overstating overdue exposure.

#### Collections Team — 60+ DPD
Per-collections-rep breakdown of accounts 60 or more days past due. Shows each rep's assigned accounts with balances and days-past-due counts. Supports drill-down to account-level detail. This tab is the primary working view for the collections team during daily standups.

#### Collections Team — Full Portfolio
All open accounts by collections rep, showing total open balance and total past-due balance (not restricted to 60+ DPD). Includes a YayPay aging report upload feature: the user can upload a YayPay summary or detailed CSV export, and the tab reconciles YayPay balances against NetSuite balances side by side, flagging discrepancies.

#### Customer 360
A real-time drill-down for any customer in the portfolio. Click any account name (from any tab) to open a live view showing:
- All open invoices with amounts, due dates, and DPD
- Salesforce flags: support hold status, legal flag, strategic account designation, CSM assignment
- Payment history
- Collections activity notes

This tab queries NetSuite and Salesforce live (not from the snapshot) so it always reflects the current state.

#### AR Analytics
Portfolio-level trend charts and distributions:
- DPD distribution (how many accounts fall into each aging bucket)
- Hold history over time
- Aging trend
- Cash collected over time

These charts are rendered from the snapshot data.

### 2.4 Pulse Deck Generator

The "Generate Pulse Deck" button (available from the main dashboard header) triggers a one-click build of Jordan Duke's weekly AR Executive Pulse PPTX. The output is pixel-identical to Jordan's established deck format.

**What the build fills automatically:**
- All headline KPI numbers (cash MTD/QTD, attainment percentages, DSO, >60 and >90 balances and movement, holds, scoreboard highlights)
- Top-10 past-due customer table with balances and drafted next-action notes
- 5 cash charts (regenerated from the AR Tracker workbook): weekly run rate, quarterly run rate, cash vs. target, total cash collected, payment methods

**What requires manual completion after download:**
- 8 aging/risk charts (>60 trend, >90 trend, root cause, total AR aging, upcoming-to-60, payments against >60, payments by timing %, integrated vs. non-integrated) — these originate from YayPay/Power BI and are not yet automated; they are carried forward as the previous week's images
- Narrative text (Decisions/Updates bullets, Risks to Cash, root-cause text on slide 7) — the builder leaves tokens for these; Jordan fills them in before distribution

**Template:** `pulse-deck-agent/pulse_template.pptx` — a tokenized version of Jordan's deck with `{{TOKEN}}` placeholders for all dynamic values and named shapes for all programmatically-filled tables and charts. Do not edit the template layout without updating `build_pulse.py` to match.

---

## 3. How to Configure and Deploy Updates

### 3.1 Local Development

**Prerequisites:** Node 20, Python 3.11, pip

```bash
cd ar-dashboard
npm install
pip install -r requirements.txt   # from the project root or pulse-deck-agent/service/
cp .env.example .env               # fill in NetSuite + Salesforce credentials
npm run dev                        # starts Vite (port 5173) + Express (port 3001)
```

Open `http://localhost:5173`. The Vite dev server proxies API calls to port 3001.

Set `PYTHON_BIN` in `.env` to the full path of your Python 3.11 executable if `python` does not resolve to 3.11 on your system.

For the Pulse Deck, set `PULSE_AR_TRACKER` in `.env` to the path of the current AR Tracker workbook download.

### 3.2 Deploying to Azure (Manual — Required Until Deployment Center is Fixed)

The production deployment is an Azure Web App for Containers running a Docker image built from the `Dockerfile` in the repo root (deploy/azure branch).

**Because the GitHub↔Azure Deployment Center OIDC connection is currently broken**, every deploy requires a manual build and push:

1. **Merge your changes** to the `deploy/azure` branch.
2. **Build the Docker image** using Azure Container Registry:
   ```bash
   az acr build --registry <your-acr-name> --image ar-dashboard:latest .
   ```
3. **Restart the Azure Web App** to pull the new image:
   ```bash
   az webapp restart --name <app-name> --resource-group <rg-name>
   ```

**When Deployment Center is reconnected:** pushes to `deploy/azure` will trigger GitHub Actions to build the Docker image and deploy automatically. The workflow file is in `.github/workflows/` on the `deploy/azure` branch.

### 3.3 Environment Variables (Azure App Settings)

All secrets are configured as Azure App Settings (not in the Docker image). Set or update them in the Azure Portal under Configuration > Application settings, or via:

```bash
az webapp config appsettings set --name <app-name> --resource-group <rg-name> \
  --settings KEY=value KEY2=value2
```

| Variable | Required | Description |
|---|---|---|
| `NS_ACCOUNT_ID` | Yes | NetSuite account ID (production: `8151367`) |
| `NS_CONSUMER_KEY` | Yes | NetSuite OAuth 1.0a consumer key |
| `NS_CONSUMER_SECRET` | Yes | NetSuite OAuth 1.0a consumer secret |
| `NS_TOKEN_ID` | Yes | NetSuite OAuth 1.0a token ID |
| `NS_TOKEN_SECRET` | Yes | NetSuite OAuth 1.0a token secret |
| `SF_CLIENT_ID` | Yes | Salesforce Connected App client ID |
| `SF_CLIENT_SECRET` | Yes | Salesforce Connected App client secret |
| `SF_INSTANCE_URL` | Yes | `https://advantive.my.salesforce.com` |
| `SF_REFRESH_TOKEN` | Yes | Salesforce OAuth 2.0 refresh token |
| `PYTHON_BIN` | Yes | Full path to Python 3.11 inside the container (e.g., `/usr/local/bin/python3.11`) |
| `REFRESH_MINUTES` | No | Snapshot auto-refresh interval in minutes (default: `5`) |
| `PULSE_AR_TRACKER` | No | Path to the AR Tracker workbook for Pulse Deck cash scalars |
| `PORT` | No | HTTP port (Azure sets this automatically; default: `3001`) |

### 3.4 Updating the Pulse Deck Template

If Jordan's deck format changes (new slides, repositioned shapes, new KPIs), the template and builder must be updated together:

1. Open `pulse-deck-agent/pulse_template.pptx` in PowerPoint.
2. Replace any new dynamic values with `{{TOKEN_NAME}}` placeholders.
3. Use PowerPoint's Selection Pane to name any new chart or table shapes that the script needs to target.
4. Update `pulse-deck-agent/build_pulse.py` to read and fill the new tokens/shapes.
5. Update `ar-dashboard/pulse/pulseData.js` to map snapshot fields to the new tokens.
6. Test locally with `python build_pulse.py pulse_data.json`.

---

## 4. Additional Technical Information

### 4.1 Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React | 19.2.6 |
| Build tool | Vite | 8.0.12 |
| Backend | Node.js + Express | Node 20, Express 5 (ES modules) |
| Data scripts | Python | 3.11 |
| NetSuite client | Custom OAuth 1.0a (ns_client.py) | — |
| Salesforce client | OAuth 2.0 refresh token (sf_client.py) | — |
| Deck generation | python-pptx, matplotlib, openpyxl | — |
| Hosting | Azure Web App for Containers | — |
| Container registry | Azure Container Registry | — |
| CI/CD | GitHub Actions (deploy/azure branch) | — |

### 4.2 AI / LLM Usage

None. This application does not use any AI or language model. All data is pulled directly from NetSuite and Salesforce; all calculations are deterministic.

### 4.3 Repository Structure

| Path | Purpose |
|---|---|
| `ar-dashboard/server.js` | Express API server — all API endpoints, Python spawning, auto-refresh scheduler |
| `ar-dashboard/src/App.jsx` | React frontend — all dashboard tabs and UI |
| `ar-dashboard/live_snapshot.py` | Pulls live data from NetSuite + Salesforce; writes `hybrid-snapshot.json` |
| `ar-dashboard/ns_client.py` | NetSuite SuiteQL client (OAuth 1.0a) |
| `ar-dashboard/sf_client.py` | Salesforce SOQL client (OAuth 2.0 refresh token) |
| `ar-dashboard/customer_detail.py` | Real-time per-customer drill-down (NetSuite + Salesforce) |
| `ar-dashboard/pulse/pulseData.js` | Maps snapshot JSON fields to Pulse Deck token values |
| `ar-dashboard/sf_auth.py` | One-time Salesforce authorization-code flow — run locally to generate `SF_REFRESH_TOKEN` |
| `ar-dashboard/.env.example` | Template for required environment variables |
| `ar-dashboard/Dockerfile` | Multi-stage Docker build (Node build stage + runtime stage with Python 3.11) |
| `pulse-deck-agent/build_pulse.py` | Fills `pulse_template.pptx` with tokens, Top-10 table, and cash charts |
| `pulse-deck-agent/charts.py` | matplotlib chart generators (Advantive plum/orange palette, Aptos font) |
| `pulse-deck-agent/ar_tracker.py` | Reads AR Tracker workbook (openpyxl) for cash scalar values |
| `pulse-deck-agent/pulse_template.pptx` | Tokenized PowerPoint template (Jordan's deck format, 11 slides) |
| `pulse-deck-agent/pulse_data.example.json` | Example data schema consumed by `build_pulse.py` |

### 4.4 Data Refresh Behavior

The snapshot is refreshed on two triggers:
- **Automatic:** every 5 minutes after server startup (interval set by `REFRESH_MINUTES`)
- **Manual:** when the user clicks the refresh button in the dashboard

A guard prevents two refreshes from running simultaneously. If a manual refresh is triggered while an automatic one is in progress, the API returns a note that refresh is already running (it does not error).

The Customer 360 tab bypasses the snapshot entirely and always queries live.

### 4.5 Exchange Rate Handling

The dashboard converts non-USD AR balances to USD for display. Exchange rates are fetched from `open.er-api.com` and cached for 1 hour. If the external API is unavailable, the app falls back to hardcoded rates (USD, AUD, EUR, GBP, CAD).

### 4.6 YayPay Aging Report Upload

The Full Portfolio tab accepts a CSV export from YayPay in either summary or detailed format. The file is parsed client-side in the browser (no server upload). The parsed balances are displayed alongside the NetSuite balances for the same accounts, allowing the user to identify discrepancies without leaving the dashboard.

### 4.7 Pulse Deck Token Reference

The deck template uses `{{TOKEN}}` placeholders filled by `build_pulse.py`. Key tokens:

| Token | Slide | Description |
|---|---|---|
| `{{WEEK_ENDING_LABEL}}` | 1 | Deck title week-ending date |
| `{{CASH_MTD}}` / `{{CASH_MTD_PCT}}` | 2 | Cash collected MTD and % of target |
| `{{CASH_QTD}}` / `{{CASH_QTD_PCT}}` | 2 | Cash collected QTD and % of target |
| `{{DSO}}` | 2 | Days Sales Outstanding |
| `{{BAL_60}}` / `{{COLL_60_WEEK}}` | 2 | >60 DPD balance and weekly collections |
| `{{BAL_90}}` / `{{COLL_90_WEEK}}` | 2 | >90 DPD balance and weekly collections |
| `{{FORECAST_CONFIDENCE}}` | 2 | Cash forecast confidence level |
| `{{AGING60_START/ROLLED_IN/COLLECTED/ENDING/TARGET/MOVEMENT}}` | 4 | >60 aging movement block |
| `{{AGING90_START/ROLLED_IN/COLLECTED/WRITEOFFS/ENDING/TARGET/MOVEMENT}}` | 10 | >90 aging movement block |
| `{{HOLDS_UNDER_THREAT}}` / `{{HOLDS_ON_HOLD}}` / `{{HOLDS_RELATED_PAYMENTS}}` | 11 | Hold counts |

Named shapes (programmatically filled):
- `tbl_top10` — Top-10 past-due customer table (slide 6)
- `tbl_top4_roll` — Top-4 likely-to-roll accounts (slide 5)
- `chart_payments_timing` — Payments by timing % chart picture (slide 9)

---

_Last updated: 2026-07-27_
_Built by Zach Bergman (Business Systems intern, Summer 2026)_
