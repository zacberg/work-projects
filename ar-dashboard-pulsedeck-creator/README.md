# AR Dashboard and Pulse Deck Creator

An internal AR collections dashboard with live data pulled from NetSuite and Salesforce, plus a one-click weekly AR Executive Pulse PowerPoint generator. Built for the Advantive Finance Operations and Collections teams.

Built by Zach Bergman (2026 summer intern, Business Systems).

**Status: Live.** Deployed to Azure and in active use by Jordan Duke and the Finance Operations team. The Pulse Deck generator is in active use for weekly AR executive reporting.

---

## What it does

The dashboard provides real-time visibility into Advantive's AR portfolio:

- **AR Overview** — total open balances, overdue balances, 60+ DPD buckets, support holds, placement queue, write-off pool, and cash collected this month
- **Collections Team — 60+ DPD** — per-rep breakdown of accounts 60 or more days past due, with drill-down account lists
- **Collections Team — Full Portfolio** — all open accounts by rep with total and past-due balances; supports a YayPay aging report upload (summary or detailed format) to reconcile YayPay balances against NetSuite
- **Customer 360** — click any account to get a live drill-down: all open invoices, Salesforce flags, support holds, payment history, and collections activity
- **AR Analytics** — DPD distribution charts, hold history, aging trend, and cash collected over time
- **Pulse Deck Generator** — one-click button that builds Jordan Duke's weekly AR Executive Pulse PPTX from live data, auto-filling all charts and KPIs in her established format

Data sources:

- **NetSuite** (production account 8151367) — all AR balances, aging, DPD, invoices, holds via SuiteQL
- **Salesforce** (advantive.my.salesforce.com) — support holds, legal flags, CSM assignments, strategic account status
- **YayPay** — optional aging report upload (summary or detailed format) to reconcile balances

---

## Architecture

The app is a single Node.js/Express service that serves the React frontend and the API on one port. Python is spawned for live data pulls and deck generation.

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite 8 |
| Backend | Node 20 + Express 5 (ES modules) |
| Data scripts | Python 3.11 |
| Live data (AR) | NetSuite SuiteQL via OAuth 1.0a (credentials in .env) |
| Live data (CRM) | Salesforce via OAuth 2.0 refresh token |
| Deck generation | python-pptx + matplotlib + openpyxl |
| Hosting | Azure Web App for Containers |

---

## Repo structure

| Path | Purpose |
|------|---------|
| `server.js` | Express API server — NetSuite/Salesforce data endpoints, YayPay upload, Pulse Deck trigger |
| `src/` | React 19 frontend (Vite) — all dashboard views and components |
| `src/App.jsx` | Main dashboard component — all tabs and data rendering |
| `scripts/` | Python data scripts — NetSuite SuiteQL queries, Salesforce API calls |
| `pulse-deck-agent/` | Pulse Deck generation scripts and template (pulse_template.pptx) |
| `Dockerfile` | Multi-stage Docker build for Azure deployment |
| `.env` | Local environment variables (not committed — see .env.example) |

---

## Local development

```bash
npm install
pip install -r requirements.txt
# Copy .env.example to .env and fill in NetSuite + Salesforce credentials
npm run dev        # starts Vite frontend (port 5173) + Node backend (port 3001)
```

The backend spawns Python scripts at runtime; ensure PYTHON_BIN in .env points to the correct Python 3.11 executable.

---

## Deployment

The production app is deployed to Azure Web App for Containers and refreshes its data from NetSuite and Salesforce on a 5-minute interval.

The deploy/azure branch is the production branch. GitHub Actions builds the Docker image and deploys it to Azure on every push to that branch.

For deployment setup, runtime configuration, and Docker details, see the deploy/azure branch README and DEPLOY.md.

---

_Last updated: 2026-07-20_