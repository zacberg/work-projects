// pulseData.js — map the dashboard's hybrid snapshot into the pulse-deck builder's
// pulse_data shape.
//
// Principle: ONLY fill fields with live data we can actually source. Everything
// else is set to a visible "[update]" marker (or a placeholder chart) — we never
// silently carry last week's numbers/graphs, because stale data shown as current
// is worse than an obvious blank.

// Clean, unobtrusive marker for values we can't source live yet (instead of the
// code-like "[update]"). Reads as "no data" on a CFO slide; Jordan fills the real
// number on review. Never carries last week's value forward.
const BLANK = "—";
// current week's AR Tracker workbook (drop the fresh download here each week)
const AR_TRACKER_PATH = process.env.PULSE_AR_TRACKER ||
  "C:/Users/ZachBergman/Downloads/2026 Advantive AR Tracker (1).xlsx";
// Full dollar amounts with thousands separators (no M/K abbreviation) so every
// number in the deck — tables, headers, and charts — reads in the same format.
const fmtUSD = (n) => `$${Math.round(Number(n) || 0).toLocaleString("en-US")}`;
const fmtM = fmtUSD;
const fmtK = fmtUSD;
const accts = (n) => `${n} Accounts`;

function weekEndingFriday(date = new Date()) {
  const d = new Date(date);
  const diff = (5 - d.getDay() + 7) % 7;
  d.setDate(d.getDate() + diff);
  const yy = String(d.getFullYear()).slice(-2);
  return `${d.getMonth() + 1}/${d.getDate()}/${yy}`;
}
const cleanName = (name) => String(name || "").split(" (")[0].trim();

// charts we can't source live yet -> replaced with a clear "pending" placeholder
const PLACEHOLDER_CHARTS = {
  chart_weekly_run_rate:           "Weekly Cash Run Rate|AR Tracker",
  chart_cash_target_vs_actual:     "Cash vs Target|AR Tracker",
  chart_cash_target_vs_actual_2:   "Cash vs Target|AR Tracker",
  chart_payment_methods:           "Payment Methods|NetSuite / AR Tracker",
  chart_gt60_trend:                ">60 Trend|YayPay",
  chart_gt90_trend:                ">90 Trend|YayPay",
  chart_root_cause:                "Root Cause|YayPay",
  chart_upcoming_to_60:            "Upcoming to >60|YayPay",
  chart_payments_against_60:       "Payments Against >60|YayPay",
  chart_payments_by_timing_pct:    "Payments by Timing %|YayPay",
  chart_payments_by_timing_dollars:"Payments by Timing $|YayPay",
  // remaining stale embedded images on slides 3 / 9 / 10
  chart_cash_s3_1:                 "Cash Chart|AR Tracker",
  chart_cash_s3_2:                 "Cash Chart|AR Tracker",
  chart_cash_s3_3:                 "Cash Chart|AR Tracker",
  chart_cash_s9_1:                 "Cash Scoreboard|AR Tracker",
  chart_cash_s9_2:                 "Cash Scoreboard|AR Tracker",
  chart_aging_s10_1:               "Payments by Timing|YayPay",
};

export function buildPulseData(snap, base) {
  // EVERY template token starts blank; we only set the ones we can source live.
  const tokenKeys = Object.keys(base.tokens || {});
  const tokens = {};
  for (const k of tokenKeys) tokens[k] = BLANK;
  const auto = [];
  const set = (k, v) => { tokens[k] = v; auto.push(k); };

  // ── live: date ──
  set("WEEK_ENDING", weekEndingFriday());

  // ── live: aging balances (invoice-level, USD; from NetSuite) ──
  // BAL_60 = the 60+ overdue balance (matches the dashboard headline + aging strip).
  // BAL_90 = invoice-level >90 balance, summed from the aging buckets for consistency.
  const aging = snap.fullAging || {};
  const bal60 = snap.overdueBalance?.total ?? 0;
  const bal90 = ["91-120", "121-180", "181-365", "365+"].reduce((s, k) => s + (aging[k] || 0), 0);
  if (bal60) { set("BAL_60", fmtM(bal60)); set("AGING60_ENDING", fmtM(bal60)); }
  if (bal90) set("BAL_90", fmtM(bal90));

  // ── live: holds ──
  if (snap.supportHolds?.onHoldCount != null) set("HOLDS_ON_HOLD", accts(snap.supportHolds.onHoldCount));
  if (snap.placementQueue?.eligibleCount != null) set("HOLDS_UNDER_THREAT", accts(snap.placementQueue.eligibleCount));
  if (snap.supportHolds?.onHoldBalance != null) set("HOLDS_RELATED_PAYMENTS", fmtM(snap.supportHolds.onHoldBalance));

  // ── live: cash collected (NetSuite CustPymt — may differ from AR Tracker official figure) ──
  const cash = snap.cashCollected;
  if (cash?.mtd != null) set("CASH_MTD", fmtM(cash.mtd));
  if (cash?.qtd != null) set("CASH_QTD", fmtM(cash.qtd));
  const movers = cash?.topMovers || [];
  movers.slice(0, 3).forEach((m, i) => set(`TOP_MOVER_${i + 1}`, `${cleanName(m.name)} - ${fmtK(m.amt)}`));

  // NOTE: left as [update] on purpose (no live source yet):
  //   *_PCT / *_ATTAINMENT / *_TARGET  -> targets live in the AR Tracker
  //   AGING60/90 movement (start/rolled/collected/writeoffs) -> need last week's snapshot
  //   SCORE_MAY_* -> scoreboard slide is hard-coded to "May" + needs targets
  //   DSO, COLL_60/90_WEEK, FORECAST_CONFIDENCE -> not sourced live yet

  // ── Top-10 past-due (live, NetSuite via repAccounts) ──
  const all = [];
  for (const [rep, list] of Object.entries(snap.repAccounts || {})) {
    for (const a of list) all.push({ ...a, rep });
  }
  all.sort((a, b) => (b.balance || 0) - (a.balance || 0));
  // Fill the live-sourced columns (customer / exposure / owner); leave the
  // narrative columns blank for Jordan to fill — never carry last week's text.
  const top10 = all.slice(0, 10).map((a) => ({
    customer: cleanName(a.name),
    exposure: fmtK(a.balance || 0),
    status: "",
    root_cause: "",
    owner: a.rep === "Unassigned" ? "" : (a.rep || ""),
    timeline: "",
    next_action: "",
  }));

  // ── live chart: aging strip ──
  let aging_buckets = null;
  if (snap.fullAging) {
    aging_buckets = {};
    for (const [k, v] of Object.entries(snap.fullAging)) if (!k.startsWith("_")) aging_buckets[k] = v;
    auto.push("chart_total_ar_aging");
  }

  // ── Slide 5 "likely to roll" cards (live, 30-59 DPD accounts approaching >60) ──
  const rollCards = (snap.approaching || []).slice(0, 4).map((a) => ({
    name: cleanName(a.name),
    amount: a.balance || 0,
    dpd: a.dpd,
  }));

  const blanked = tokenKeys.filter((k) => !auto.includes(k));
  return {
    data: { tokens, top10, roll_cards: rollCards, charts: {}, aging_buckets, placeholder_charts: PLACEHOLDER_CHARTS, ar_tracker_path: AR_TRACKER_PATH },
    autoFilled: auto,
    blanked,
    topCount: top10.length,
  };
}
