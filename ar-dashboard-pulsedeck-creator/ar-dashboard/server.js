import express from "express";
import cors from "cors";
import { readFileSync, writeFileSync, mkdtempSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { tmpdir } from "os";
import { spawn } from "child_process";
import dotenv from "dotenv";
import { buildPulseData } from "./pulse/pulseData.js";

dotenv.config();

// the pulse-deck builder lives in the sibling folder
const PULSE_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "pulse-deck-agent");

const __dirname = dirname(fileURLToPath(import.meta.url));

// Python interpreter for spawned scripts. The bare "python" can resolve to the
// Windows Store App-Execution-Alias stub, which fails silently (non-zero exit,
// no stderr) when spawned non-interactively. Pin to a real interpreter; override
// via PYTHON_BIN in .env if the path changes.
const PYTHON_BIN = process.env.PYTHON_BIN || "python";

const app = express();
app.use(cors());
app.use(express.json());

// ── Exchange rates — fetch live, fall back to hardcoded ──
let cachedRates = null;
let ratesFetchedAt = null;

async function getExchangeRates() {
  const oneHour = 60 * 60 * 1000;
  if (cachedRates && ratesFetchedAt && Date.now() - ratesFetchedAt < oneHour) {
    return cachedRates;
  }
  try {
    const res = await fetch("https://open.er-api.com/v6/latest/USD");
    const json = await res.json();
    if (json.rates) {
      cachedRates = json.rates;
      ratesFetchedAt = Date.now();
      return cachedRates;
    }
  } catch (e) {
    console.log("Exchange rate fetch failed, using fallback rates");
  }
  return { USD: 1, AUD: 1.575, EUR: 0.922, GBP: 0.787, CAD: 1.369 };
}

// ── Hybrid snapshot (NetSuite financials + Salesforce flags) ──
function getSnapshot() {
  const raw = readFileSync(join(__dirname, "hybrid-snapshot.json"), "utf-8");
  return JSON.parse(raw);
}

app.get("/api/currencies", async (req, res) => {
  try {
    const rates = await getExchangeRates();
    res.json({ rates, fetchedAt: ratesFetchedAt || Date.now() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get("/api/dashboard", (req, res) => {
  try {
    res.json(getSnapshot());
  } catch (err) {
    console.error("Dashboard API error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Generate the AR Executive Pulse deck from live snapshot data ──
app.get("/api/pulse-deck", (req, res) => {
  try {
    const snap = getSnapshot();
    const base = JSON.parse(readFileSync(join(PULSE_DIR, "pulse_data.example.json"), "utf-8"));
    const { data, autoFilled, blanked, topCount } = buildPulseData(snap, base);

    const work = mkdtempSync(join(tmpdir(), "pulse-"));
    const dataPath = join(work, "pulse_data.json");
    const safeLabel = String(data.tokens.WEEK_ENDING).replace(/[\/\\:]/g, ".");
    const outPath = join(work, `AR Executive Pulse Week Ending ${safeLabel}.pptx`);
    writeFileSync(dataPath, JSON.stringify(data));

    const py = spawn(PYTHON_BIN, ["build_pulse.py", dataPath, "--out", outPath], { cwd: PULSE_DIR });
    let stderr = "";
    py.stderr.on("data", (d) => (stderr += d.toString()));
    py.stdout.on("data", (d) => console.log("[pulse]", d.toString().trim()));
    py.on("error", (e) => res.status(500).json({ error: `Could not run builder: ${e.message}` }));
    py.on("close", (code) => {
      if (code !== 0 || !existsSync(outPath)) {
        console.error("[pulse] build failed:", stderr);
        return res.status(500).json({ error: "Deck build failed", detail: stderr.slice(-600) });
      }
      console.log(`[pulse] live-filled ${autoFilled.length} fields, ${topCount} Top-10 rows; ${blanked.length} fields blanked [update]`);
      res.download(outPath);
    });
  } catch (e) {
    console.error("[pulse] error:", e.message);
    res.status(500).json({ error: e.message });
  }
});

// ── Live refresh from NetSuite (+ Salesforce) — shared by the manual button and
//    the server-side scheduler, with a guard so two pulls never overlap. ──
let refreshing = false;
let lastRefreshAt = null;
function runLiveRefresh() {
  return new Promise((resolve, reject) => {
    if (refreshing) return reject(new Error("refresh already in progress"));
    refreshing = true;
    const py = spawn(PYTHON_BIN, ["live_snapshot.py"], { cwd: __dirname });
    let err = "";
    py.stdout.on("data", (d) => console.log("[refresh]", d.toString().trim()));
    py.stderr.on("data", (d) => (err += d.toString()));
    py.on("error", (e) => { refreshing = false; reject(e); });
    py.on("close", (code) => {
      refreshing = false;
      if (code !== 0) return reject(new Error(err.slice(-600) || "live refresh failed"));
      lastRefreshAt = new Date().toISOString();
      resolve();
    });
  });
}

app.post("/api/refresh", async (req, res) => {
  console.log("[refresh] manual pull from NetSuite...");
  try {
    await runLiveRefresh();
    res.json({ ok: true, generatedAt: getSnapshot()._generatedAt });
  } catch (e) {
    const msg = String(e.message || e);
    if (msg.includes("in progress")) return res.json({ ok: true, note: "auto-refresh already running" });
    res.status(500).json({ error: "Live refresh failed", detail: msg.slice(-600) });
  }
});

// ── Live Customer 360 drill-down (real-time NetSuite + Salesforce, not the snapshot) ──
app.get("/api/customer", (req, res) => {
  const id = String(req.query.entity || "").replace(/[^0-9]/g, "");
  if (!id) return res.status(400).json({ error: "numeric ?entity= required" });
  const py = spawn(PYTHON_BIN, ["customer_detail.py", id], { cwd: __dirname });
  let out = "", err = "";
  py.stdout.on("data", (d) => (out += d.toString()));
  py.stderr.on("data", (d) => (err += d.toString()));
  py.on("error", (e) => res.status(500).json({ error: `Could not run lookup: ${e.message}` }));
  py.on("close", (code) => {
    if (code !== 0) return res.status(500).json({ error: "Live lookup failed", detail: err.slice(-400) });
    try { res.json(JSON.parse(out)); }
    catch (e) { res.status(500).json({ error: "Bad lookup output", raw: out.slice(0, 200) }); }
  });
});

// ── Serve built frontend ──
const distPath = join(__dirname, "dist");
app.use(express.static(distPath));
app.get("/{*path}", (req, res) => {
  res.sendFile(join(distPath, "index.html"));
});

const PORT = process.env.PORT || 3001;
const REFRESH_MIN = Number(process.env.REFRESH_MINUTES || 5);
app.listen(PORT, () => {
  console.log(`AR Dashboard → http://localhost:${PORT}`);
  console.log(`Mode: Hybrid snapshot (NetSuite + Salesforce)`);
  try { console.log(`Data as of: ${getSnapshot()._generatedAt}`); } catch {}

  // ── Server-side auto-refresh: keep the snapshot live from NetSuite + Salesforce
  //    on a fixed interval, independent of any browser. All features read this. ──
  console.log(`Auto-refresh: every ${REFRESH_MIN} min (live NetSuite + Salesforce)`);
  const tick = () => runLiveRefresh()
    .then(() => console.log(`[auto-refresh] snapshot updated @ ${lastRefreshAt}`))
    .catch((e) => console.error("[auto-refresh] skipped:", String(e.message).slice(-160)));
  setInterval(tick, REFRESH_MIN * 60 * 1000);
  setTimeout(tick, 5000); // initial pull shortly after boot (doesn't block startup)
});
