import { useState, useEffect, useCallback, useRef } from "react";
import "./App.css";

const CHATGPT_URL = "https://chatgpt.com/agents/a/agt_6a15f08cfee88191a482fde7a9d4cff5";
const API_BASE    = "";
const REFRESH_SEC = 60; // UI polls the server-maintained live snapshot every 60s

function fmt(n) {
  if (!n && n !== 0) return "—";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}

// ── Animated counter ─────────────────────────────────────────────────
function useCounter(target, duration = 800) {
  const [val, setVal] = useState(0);
  const prev = useRef(0);
  useEffect(() => {
    if (target === 0 || target == null) { setVal(0); return; }
    const start = prev.current, diff = target - start, t0 = performance.now();
    const tick = now => {
      const p = Math.min((now - t0) / duration, 1);
      setVal(Math.round(start + diff * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(tick); else prev.current = target;
    };
    requestAnimationFrame(tick);
  }, [target, duration]);
  return val;
}
const AnimatedDollar = ({ value }) => <>{fmt(useCounter(value))}</>;
const AnimatedCount  = ({ value }) => <>{useCounter(value)}</>;
const Skel = ({ h = 20 }) => <div className="skeleton" style={{ height: h }} />;

// Self-contained refresh countdown — isolates the 1s tick so the whole app
// does NOT re-render every second (that per-second re-render was repainting the
// blurred panel overlay and making panels flicker/flash open & closed).
function RefreshCountdown({ seconds, onElapse }) {
  const [left, setLeft] = useState(seconds);
  const cb = useRef(onElapse);
  cb.current = onElapse;
  const deadline = useRef(Date.now() + seconds * 1000);
  useEffect(() => {
    deadline.current = Date.now() + seconds * 1000;
    setLeft(seconds);
    // Drive off a wall-clock deadline so the callback fires from the interval
    // handler (a normal context) — never from inside a setState updater.
    const t = setInterval(() => {
      const remaining = Math.round((deadline.current - Date.now()) / 1000);
      if (remaining <= 0) {
        deadline.current = Date.now() + seconds * 1000;
        setLeft(seconds);
        cb.current && cb.current();
      } else {
        setLeft(remaining);
      }
    }, 1000);
    return () => clearInterval(t);
  }, [seconds]);
  return <span className="app-countdown"> · auto-refresh in {left}s</span>;
}

// ── Prompt builder ────────────────────────────────────────────────────
function buildPrompt(key, data) {
  if (!data) return "";
  const d = data;
  const today = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

  const prompts = {
    morningBriefing: `Morning briefing for ${today}.

PORTFOLIO OVERVIEW (NetSuite)
- Total overdue (60+ DPD): ${fmt(d.overdueBalance?.total)} across ${d.overdueBalance?.accountCount} accounts
- At risk (60+ DPD): ${fmt(d.atRisk?.total)} across ${d.atRisk?.accountCount} accounts

HOLD STATUS
- Active support holds (SF): ${d.supportHolds?.onHoldCount} accounts (${fmt(d.supportHolds?.onHoldBalance)})
- Missing holds: ${d.supportHolds?.missingHoldCount} accounts qualify but aren't on hold (${fmt(d.supportHolds?.missingHoldBalance)})
- NS vs SF discrepancy: ${d.holdsComparison?.nsUnmatchedHoldCount} SF holds have no matching NS invoice

ACTION QUEUES
- TAA placement eligible: ${d.placementQueue?.eligibleCount} accounts (${fmt(d.placementQueue?.eligibleBalance)}), ${d.placementQueue?.blockedCount} blocked
- Write-off candidates (180+ DPD): ${d.writeOffPool?.candidateCount} accounts (${fmt(d.writeOffPool?.candidateBalance)})
- Demand letter eligible: ${d.demandLetterQueue?.count} accounts (${fmt(d.demandLetterQueue?.balance)})

COLLECTIONS TEAM
${d.taaChecks?.inactiveReps?.length ? `⚠ INACTIVE REPS: ${d.taaChecks.inactiveReps.map(r => `${r.repName} (${r.accountCount} accts)`).join(", ")} — reassign before TAA placement` : "All reps verified active"}
- Accounts missing account manager: ${d.taaChecks?.withoutManagerCount} / ${d.taaChecks?.eligibleCount}

RISK FLAGS
- Legal/bankruptcy holds: ${d.legalBlocked?.count} accounts (${fmt(d.legalBlocked?.balance)})
- Extreme DPD (365+): ${d.extremeDPD?.count} accounts (${fmt(d.extremeDPD?.balance)})
- Stop hold overrides: ${d.stopHoldOverrides?.count} accounts (${fmt(d.stopHoldOverrides?.balance)})
- Strategic accounts overdue: ${d.strategicWatch?.count} accounts (${fmt(d.strategicWatch?.balance)})

Based on this state, what are the highest-priority actions today? Run the relevant workflows for the most urgent items.`,

    atRisk: `We currently have ${d.atRisk?.accountCount} accounts at 60+ days past due totaling ${fmt(d.atRisk?.total)}.

Top accounts:
${d.atRisk?.topAccounts?.map(a => `- ${a.name}: ${fmt(a.balance)} (${Math.round(a.dpd)} DPD)`).join("\n")}

Pull the full 60+ DPD list from NetSuite. Show total balance, account count, and all accounts by overdue balance. Flag any with legal holds, bankruptcy holds, or active support holds.`,

    overdueBalance: `Our total overdue portfolio (60+ DPD) is ${fmt(d.overdueBalance?.total)} across ${d.overdueBalance?.accountCount} accounts.

DPD breakdown:
${d.dpdBreakdown?.map(r => `- ${r.bucket}: ${r.accounts} accounts, ${fmt(r.balance)}`).join("\n")}

Pull from NetSuite, show account count and balance per tier, flag any notable concentrations.`,

    dpdBreakdown: `DPD breakdown as of today:
${d.dpdBreakdown?.map(r => `- ${r.bucket}: ${r.accounts} accounts, ${fmt(r.balance)}`).join("\n")}

Run a full DPD breakdown from NetSuite. Show account counts, total balances, and flag 365+ DPD accounts for data quality review.`,

    supportHolds: `Hold audit (SF holds cross-referenced with NetSuite AR):
- Active holds: ${d.supportHolds?.onHoldCount} accounts (${fmt(d.supportHolds?.onHoldBalance)})
- Missing holds: ${d.supportHolds?.missingHoldCount} accounts qualify but aren't on hold (${fmt(d.supportHolds?.missingHoldBalance)})
- NS vs SF discrepancy: ${d.holdsComparison?.sfHoldCount} SF holds, ${d.holdsComparison?.nsUnmatchedHoldCount} have no matching NetSuite invoice

Run the full support hold audit. Show release candidates, the ${d.supportHolds?.missingHoldCount} missing holds that meet the 45-DPD threshold, and flag accounts on hold in SF with no open NS invoice (stale holds).`,

    placementQueue: `TAA (Tucker Albin & Associates) placement queue:
- Eligible: ${d.placementQueue?.eligibleCount} accounts (${fmt(d.placementQueue?.eligibleBalance)})
- Blocked: ${d.placementQueue?.blockedCount} accounts
${d.taaChecks?.inactiveReps?.length ? `\n⚠ INACTIVE REPS: ${d.taaChecks.inactiveReps.map(r => r.repName).join(", ")} — verify before placing their accounts` : ""}
- Accounts without account manager: ${d.taaChecks?.withoutManagerCount} — assign AM before TAA placement

Top eligible accounts:
${d.placementQueue?.topAccounts?.map(a => `- ${a.name}: ${fmt(a.balance)} (${Math.round(a.dpd)} DPD)`).join("\n")}

Run the third-party placement tracker. Pull all eligible accounts, apply legal screening, give the TAA-ready list by collections rep. Verify account manager is assigned in NetSuite before placing.`,

    writeOffPool: `Write-off pool: ${d.writeOffPool?.candidateCount} candidates totaling ${fmt(d.writeOffPool?.candidateBalance)} at 180+ DPD.

Top candidates:
${d.writeOffPool?.topAccounts?.map(a => `- ${a.name}: ${fmt(a.balance)} (${Math.round(a.dpd)} DPD)`).join("\n")}

Run the write-off and decommission workflow. Apply legal screening, draft rationales, show approval tier breakdown.`,

    legalBlocked: `${d.legalBlocked?.count} accounts blocked by litigation or bankruptcy holds (${fmt(d.legalBlocked?.balance)}).

Run the legal exclusion check. Pull all accounts with litigation/bankruptcy holds. Classify each as Blocked or Review Flag and include the matching legal text.`,

    demandLetterQueue: `${d.demandLetterQueue?.count} accounts totaling ${fmt(d.demandLetterQueue?.balance)} eligible for demand letters — 60+ DPD, not legally blocked, not placed.

Run demand letter automation. Pre-check legal first, then draft letters for highest-balance eligible accounts.`,

    extremeDPD: `${d.extremeDPD?.count} accounts at 365+ DPD totaling ${fmt(d.extremeDPD?.balance)}.

For each account show: Name | DPD | Balance | Legal flag | Hold status | TAA placed
Classify as: WRITE-OFF CANDIDATE / DATA QUALITY REVIEW / TAA RISK`,

    stopHoldOverrides: `${d.stopHoldOverrides?.count} accounts with Stop Hold Override active at 30+ DPD (${fmt(d.stopHoldOverrides?.balance)}).

Run payment plan risk review for each — flag renewal timing conflicts, broken-plan history, and hold-override risk.`,

    strategicWatch: `${d.strategicWatch?.count} strategic accounts at 30+ DPD (${fmt(d.strategicWatch?.balance)}).

Pull all Strategic Accounts with overdue balances. Show balance, DPD, CSM assignment. No holds or placement — CSM coordination required. Flag any approaching 60 DPD.`,

    possiblePendingHolds: `${d.possiblePendingHolds?.count} accounts flagged as possible pending hold, not yet on hold (${fmt(d.possiblePendingHolds?.balance)}).

Run hold criteria check — apply 45-DPD minimum and 15% ARR threshold. Show which accounts formally qualify for a hold recommendation pending Jordan Duke's approval.`,

    collectionsReps: `Collections rep breakdown (60+ DPD):
${d.collectionsReps?.map(r => `- ${r.rep}: ${r.accounts} accounts, ${fmt(r.balance)}`).join("\n")}

Pull a full rep breakdown from NetSuite. For each rep show account count, total overdue balance, top 3 accounts, and any with legal or support holds that need escalation.`,
  };

  return prompts[key] || "";
}

// ── Priorities ────────────────────────────────────────────────────────
function getPriorities(data) {
  if (!data) return [];
  const d = data;
  const items = [];

  const inactiveReps = d.taaChecks?.inactiveReps || [];
  if (inactiveReps.length > 0)
    items.push({
      severity: "urgent",
      title: `${inactiveReps.length} Collections Rep${inactiveReps.length > 1 ? "s" : ""} May Be Inactive`,
      detail: `${inactiveReps.map(r => `${r.repName} (${r.accountCount} accts)`).join(", ")} — verify and reassign before TAA placement`,
      promptKey: "placementQueue", label: "Review & Reassign →",
    });

  if (d.supportHolds?.missingHoldCount > 0)
    items.push({
      severity: d.supportHolds.missingHoldCount > 150 ? "urgent" : "warning",
      title: `${d.supportHolds.missingHoldCount} Accounts Need Support Holds`,
      detail: `${fmt(d.supportHolds.missingHoldBalance)} in unprotected accounts qualify for a hold`,
      promptKey: "supportHolds", label: "Run Hold Audit →",
    });

  if (d.extremeDPD?.count > 0)
    items.push({
      severity: "urgent",
      title: `${d.extremeDPD.count} Accounts at 365+ DPD`,
      detail: `${fmt(d.extremeDPD.balance)} — data quality review required before TAA submission`,
      promptKey: "extremeDPD", label: "Review Extreme DPD →",
    });

  if (d.placementQueue?.eligibleCount > 0)
    items.push({
      severity: "warning",
      title: `${d.placementQueue.eligibleCount} Accounts Ready for TAA`,
      detail: `${fmt(d.placementQueue.eligibleBalance)} eligible — ${d.placementQueue.blockedCount} blocked, ${d.taaChecks?.withoutManagerCount || 0} missing account manager`,
      promptKey: "placementQueue", label: "Run Placement Tracker →",
    });

  if (d.writeOffPool?.candidateCount > 0)
    items.push({
      severity: "info",
      title: `${d.writeOffPool.candidateCount} Write-Off Candidates`,
      detail: `${fmt(d.writeOffPool.candidateBalance)} at 180+ DPD — rationales and approvals needed`,
      promptKey: "writeOffPool", label: "Run Write-Off Workflow →",
    });

  if (d.legalBlocked?.count > 0)
    items.push({
      severity: "urgent",
      title: `${d.legalBlocked.count} Accounts Legally Blocked`,
      detail: `${fmt(d.legalBlocked.balance)} — litigation or bankruptcy holds active`,
      promptKey: "legalBlocked", label: "Run Legal Screen →",
    });

  return items.sort((a, b) => ({ urgent: 0, warning: 1, info: 2 }[a.severity] - { urgent: 0, warning: 1, info: 2 }[b.severity])).slice(0, 5);
}

// ── Prompt panel ──────────────────────────────────────────────────────
function PromptPanel({ promptKey, label, data, onClose }) {
  const [copied, setCopied] = useState(false);
  const [opened, setOpened] = useState(false);
  const prompt = buildPrompt(promptKey, data);

  const handleCopy = () => { navigator.clipboard.writeText(prompt); setCopied(true); setTimeout(() => setCopied(false), 3000); };
  const handleOpen = () => { navigator.clipboard.writeText(prompt); setCopied(true); setOpened(true); window.open(CHATGPT_URL, "_blank"); };

  return (
    <div className="panel-overlay" onClick={onClose}>
      <div className="panel" onClick={e => e.stopPropagation()}>
        <div className="panel-header">
          <span className="panel-title">{label}</span>
          <button className="panel-close" onClick={onClose}>✕</button>
        </div>
        <pre className="panel-prompt">{prompt}</pre>
        {opened ? (
          <div className="paste-reminder">
            <div className="paste-reminder-icon">📋</div>
            <div className="paste-reminder-text">
              <strong>Prompt copied — switch to ChatGPT and press</strong>
              <kbd>Ctrl</kbd> + <kbd>V</kbd> <span>to paste, then hit Enter</span>
            </div>
            <button className="paste-reminder-close" onClick={onClose}>Done</button>
          </div>
        ) : (
          <div className="panel-actions">
            <button className={`panel-btn panel-btn--copy${copied ? " panel-btn--copied" : ""}`} onClick={handleCopy}>{copied ? "✓ Copied!" : "Copy Prompt"}</button>
            <button className="panel-btn panel-btn--open" onClick={handleOpen}>Copy &amp; Open ChatGPT →</button>
          </div>
        )}
        <p className="panel-hint">{opened ? "ChatGPT opened — paste prompt and hit Enter." : "Prompt includes live NetSuite numbers."}</p>
      </div>
    </div>
  );
}

function LaunchButton({ promptKey, label = "Launch in Agent →", data }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="launch-btn" onClick={() => setOpen(true)}>{label}</button>
      {open && <PromptPanel promptKey={promptKey} label={label} data={data} onClose={() => setOpen(false)} />}
    </>
  );
}

// ── Holds comparison panel ────────────────────────────────────────────
function HoldsComparisonPanel({ data, onClose }) {
  const hc = data?.holdsComparison;
  if (!hc) return null;
  return (
    <div className="panel-overlay" onClick={onClose}>
      <div className="panel" onClick={e => e.stopPropagation()}>
        <div className="panel-header">
          <span className="panel-title">NS vs SF Holds — Full List</span>
          <button className="panel-close" onClick={onClose}>✕</button>
        </div>
        <div className="holds-comparison">
          <div className="hc-row hc-header"><span>System</span><span>Count</span><span>Notes</span></div>
          <div className="hc-row"><span>Salesforce</span><span className="hc-val">{hc.sfHoldCount}</span><span>{hc.nsMatchedHoldCount} matched to open NS invoices</span></div>
          <div className="hc-row hc-warn"><span>SF hold, no NS invoice</span><span className="hc-val">{hc.nsUnmatchedHoldCount}</span><span>Verify in NetSuite — possible stale holds</span></div>
          <div className="hc-row"><span>NetSuite (paymenthold)</span><span className="hc-val">0</span><span>NS payment hold field not in use for ADV</span></div>
        </div>
        {hc.sfHolds?.length > 0 && (
          <div className="acct-list" style={{ maxHeight: 320, overflowY: "auto" }}>
            {hc.sfHolds.map((h, i) => (
              <div key={i} className="acct-row">
                <span className="acct-name">{h.name}</span>
                <span className="acct-meta">{h.accountManager || "No AM"} · {h.rep || "No rep"}</span>
              </div>
            ))}
          </div>
        )}
        <div className="panel-actions"><button className="panel-btn panel-btn--copy" onClick={onClose}>Close</button></div>
      </div>
    </div>
  );
}

// ── TAA checks panel ──────────────────────────────────────────────────
function TAAChecksPanel({ data, onClose }) {
  const tc = data?.taaChecks;
  if (!tc) return null;
  return (
    <div className="panel-overlay" onClick={onClose}>
      <div className="panel" onClick={e => e.stopPropagation()}>
        <div className="panel-header">
          <span className="panel-title">TAA Placement Checks</span>
          <button className="panel-close" onClick={onClose}>✕</button>
        </div>
        <div className="taa-checks">
          <div className="taa-section">
            <div className="taa-section-title">Account Manager Coverage</div>
            <div className="taa-stat-row"><span className="taa-stat-ok">{tc.withManagerCount}</span><span className="taa-stat-label">have an account manager in Salesforce</span></div>
            <div className="taa-stat-row"><span className="taa-stat-warn">{tc.withoutManagerCount}</span><span className="taa-stat-label">missing account manager — assign before TAA placement</span></div>
          </div>
          {tc.inactiveReps?.length > 0 && (
            <div className="taa-section">
              <div className="taa-section-title">Potentially Inactive Reps</div>
              <p className="taa-section-note">These reps appear on open NetSuite invoices but are not assigned in Salesforce. Verify they are still active Advantive employees before submitting their accounts to TAA.</p>
              <div className="acct-list">
                {tc.inactiveReps.map((r, i) => (
                  <div key={i} className="acct-row">
                    <span className="acct-name">{r.repName}</span>
                    <span className="acct-meta taa-stat-warn">{r.accountCount} open accounts</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="panel-actions"><button className="panel-btn panel-btn--copy" onClick={onClose}>Close</button></div>
      </div>
    </div>
  );
}

// ── Section header ────────────────────────────────────────────────────
function SectionHeader({ title, sub, source }) {
  return (
    <div className="section-header">
      <div className="section-header-text">
        <div className="section-title">{title}</div>
        {sub && <div className="section-sub">{sub}</div>}
      </div>
      <div className="section-line" />
      {source && <SourceTag source={source} />}
    </div>
  );
}

// ── Inactive rep banner ───────────────────────────────────────────────
function InactiveRepBanner({ data }) {
  const reps = data?.taaChecks?.inactiveReps;
  if (!reps?.length) return null;
  const totalAccounts = reps.reduce((s, r) => s + r.accountCount, 0);
  return (
    <div className="inactive-banner">
      <div className="inactive-banner-icon">⚠️</div>
      <div className="inactive-banner-content">
        <strong>Action Required — Reassign accounts from potentially inactive reps</strong>
        <p>{reps.length} collections rep{reps.length > 1 ? "s" : ""} appear on open NetSuite invoices but are no longer assigned in Salesforce. {totalAccounts} account{totalAccounts > 1 ? "s" : ""} may be unworked.</p>
        <div className="inactive-banner-chips">
          {reps.map((r, i) => (
            <span key={i} className="inactive-chip">
              {r.repName} <span className="inactive-chip-count">{r.accountCount} accts</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── KPI card ──────────────────────────────────────────────────────────
function SourceTag({ source }) {
  if (!source) return null;
  const label = source === "ns" ? "NetSuite" : "Salesforce";
  return <span className={`src-tag src-tag--${source}`} title={source === "ns" ? "Live source of truth — NetSuite" : "Secondary — Salesforce (snapshot until live)"}>{label}</span>;
}

function KPICard({ color, label, value, sub, topAccounts, promptKey, launchLabel, data, source, onDrill }) {
  return (
    <div className={`kpi-card kpi-card--${color}`}>
      <div className="kpi-label-row">
        <span className="kpi-label">{label}</span>
        <SourceTag source={source} />
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-sub">{sub}</div>
      {topAccounts?.length > 0 && (
        <div className="kpi-footer">
          <div className="kpi-top-accounts">
            {topAccounts.slice(0, 3).map((a, i) => (
              <div key={i}
                   className={`kpi-account-row${a.id ? " kpi-account-row--click" : ""}`}
                   onClick={a.id && onDrill ? () => onDrill(a.id, a.name) : undefined}
                   title={a.id ? "View live NetSuite + Salesforce detail" : undefined}>
                <span className="kpi-account-name">{a.name}</span>
                <span className="kpi-account-meta">{fmt(a.balance)} · {Math.round(a.dpd)}d</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <LaunchButton promptKey={promptKey} label={launchLabel} data={data} />
    </div>
  );
}

// ── Collections Team ──────────────────────────────────────────────────
function CollectionsTeamSection({ data, loading }) {
  const [expanded, setExpanded] = useState({});
  const toggle = rep => setExpanded(e => ({ ...e, [rep]: !e[rep] }));

  const reps = data?.collectionsReps || [];
  const repAccounts = data?.repAccounts || {};
  const inactiveNames = new Set((data?.taaChecks?.inactiveReps || []).map(r => r.repName));
  const maxBalance = Math.max(...reps.map(r => r.balance), 1);

  const sorted = [...reps].sort((a, b) => {
    const aInactive = inactiveNames.has(a.rep) ? 0 : a.rep === "Unassigned" ? 1 : 2;
    const bInactive = inactiveNames.has(b.rep) ? 0 : b.rep === "Unassigned" ? 1 : 2;
    if (aInactive !== bInactive) return aInactive - bInactive;
    return b.balance - a.balance;
  });

  if (loading) return (
    <div className="collections-team-card">
      {[...Array(5)].map((_, i) => <div key={i} style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-soft)" }}><Skel /></div>)}
    </div>
  );

  return (
    <div className="collections-team-card">
      <div className="ct-table-header">
        <div className="ct-col-head" />
        <div className="ct-col-head">Rep</div>
        <div className="ct-col-head">Portfolio</div>
        <div className="ct-col-head ct-col-head--right">Balance</div>
        <div className="ct-col-head ct-col-head--right">Accounts</div>
        <div className="ct-col-head" />
      </div>

      {sorted.map(r => {
        const isInactive   = inactiveNames.has(r.rep);
        const isUnassigned = r.rep === "Unassigned";
        const accts = repAccounts[r.rep] || [];
        const isOpen = expanded[r.rep];
        const rowClass = `ct-rep-row${isInactive ? " inactive" : isUnassigned ? " unassigned" : ""}${isOpen ? " open" : ""}`;

        return (
          <div key={r.rep}>
            <div className={rowClass} onClick={() => accts.length && toggle(r.rep)}>
              <div>
                <div className={`ct-status-dot ct-status-dot--${isInactive ? "inactive" : isUnassigned ? "unassigned" : "active"}`} />
              </div>
              <div>
                <span className="ct-rep-name">{r.rep}</span>
                {isInactive   && <span className="ct-rep-badge ct-rep-badge--inactive">INACTIVE</span>}
                {isUnassigned && <span className="ct-rep-badge ct-rep-badge--unassigned">UNASSIGNED</span>}
              </div>
              <div className="ct-bar-cell">
                <div className="ct-bar-track">
                  <div
                    className={`ct-bar-fill ct-bar-fill--${isInactive ? "inactive" : isUnassigned ? "unassigned" : "active"}`}
                    style={{ width: `${(r.balance / maxBalance) * 100}%` }}
                  />
                </div>
              </div>
              <div className="ct-val">{fmt(r.balance)}</div>
              <div className="ct-acct-count">{r.accounts} acct{r.accounts !== 1 ? "s" : ""}</div>
              <div>
                {accts.length > 0 && (
                  <button className={`ct-expand-btn${isOpen ? " open" : ""}`} onClick={e => { e.stopPropagation(); toggle(r.rep); }}>›</button>
                )}
              </div>
            </div>

            {isOpen && accts.length > 0 && (
              <div className="ct-accounts">
                {accts.map((a, i) => (
                  <div key={i} className="ct-account-row">
                    <div />
                    <div className="ct-account-name">{a.name}</div>
                    <div />
                    <div className="ct-account-balance">{fmt(a.balance)}</div>
                    <div className={`ct-account-dpd${a.dpd >= 180 ? " ct-account-dpd--hot" : a.dpd >= 90 ? " ct-account-dpd--warn" : ""}`}>{a.dpd}d</div>
                    <div />
                  </div>
                ))}
                {r.accounts > accts.length && (
                  <div className="ct-more-row">+ {r.accounts - accts.length} more accounts</div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PriorityItem({ item, data }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className={`priority-item priority-item--${item.severity}`}>
        <div className={`priority-dot priority-dot--${item.severity}`} />
        <div className="priority-content">
          <div className="priority-title">{item.title}</div>
          <div className="priority-detail">{item.detail}</div>
        </div>
        <button className="priority-action" onClick={() => setOpen(true)}>{item.label}</button>
      </div>
      {open && <PromptPanel promptKey={item.promptKey} label={item.label} data={data} onClose={() => setOpen(false)} />}
    </>
  );
}

// ── Priorities section ────────────────────────────────────────────────
function PrioritiesSection({ data, loading }) {
  const [briefOpen, setBriefOpen] = useState(false);
  const priorities = getPriorities(data);
  return (
    <div className="priorities-section">
      <div className="priorities-header">
        <div>
          <div className="priorities-title">Today's Priorities</div>
          <div className="priorities-sub">Surfaced from NetSuite + Salesforce data</div>
        </div>
        <button className="briefing-btn" onClick={() => setBriefOpen(true)} disabled={!data}>☀ Morning Briefing</button>
      </div>
      {loading
        ? <div className="priority-list">{[...Array(3)].map((_, i) => <Skel key={i} h={56} />)}</div>
        : <div className="priority-list">
            {priorities.map((p, i) => <PriorityItem key={i} item={p} data={data} />)}
          </div>
      }
      {briefOpen && <PromptPanel promptKey="morningBriefing" label="Morning Briefing" data={data} onClose={() => setBriefOpen(false)} />}
    </div>
  );
}

// ── Tiles ─────────────────────────────────────────────────────────────
function DPDTile({ d, loading, data }) {
  const max = d ? Math.max(...d.map(r => r.balance), 1) : 1;
  return (
    <div className="tile">
      <div className="tile-header"><span className="tile-label">DPD Breakdown</span><SourceTag source="ns" /></div>
      {loading ? <>{[...Array(5)].map((_, i) => <Skel key={i} h={14} />)}</> :
        <div className="dpd-chart">
          {d?.map(r => (
            <div key={r.bucket} className="dpd-row">
              <span className="dpd-bucket">{r.bucket}</span>
              <div className="dpd-track"><div className="dpd-fill" style={{ width: `${(r.balance / max) * 100}%` }} /></div>
              <span className="dpd-balance">{fmt(r.balance)}</span>
              <span className="dpd-count">{r.accounts} accts</span>
            </div>
          ))}
        </div>
      }
      <LaunchButton promptKey="dpdBreakdown" label="Run DPD Report →" data={data} />
    </div>
  );
}

function HoldsTile({ d, loading, data }) {
  const [compOpen, setCompOpen] = useState(false);
  const hc = data?.holdsComparison;
  return (
    <div className="tile">
      <div className="tile-header"><span className="tile-label">Support Holds</span><SourceTag source="sf" /></div>
      {loading ? <><Skel h={60} /><Skel h={120} /></> : <>
        <div className="holds-grid">
          <div className="holds-cell">
            <div className="holds-num"><AnimatedCount value={d?.onHoldCount} /></div>
            <div className="holds-key">Active Holds (SF)</div>
            <div className="holds-bal">{fmt(d?.onHoldBalance)}</div>
          </div>
          <div className="holds-divider" />
          <div className="holds-cell holds-cell--warn">
            <div className="holds-num"><AnimatedCount value={d?.missingHoldCount} /></div>
            <div className="holds-key">Missing Holds</div>
            <div className="holds-bal">{fmt(d?.missingHoldBalance)}</div>
          </div>
        </div>
        {hc && (
          <div className="holds-recon">
            <div className="holds-recon-title">NS vs SF Reconciliation</div>
            <div className="holds-recon-row">
              <span>Salesforce holds</span>
              <span className="holds-recon-val holds-recon-sf">{hc.sfHoldCount}</span>
            </div>
            <div className="holds-recon-row">
              <span>Matched in NetSuite</span>
              <span className="holds-recon-val holds-recon-ok">{hc.nsMatchedHoldCount}</span>
            </div>
            <div className="holds-recon-row holds-recon-row--alert">
              <span>⚠ SF hold, no NS invoice</span>
              <span className="holds-recon-val holds-recon-warn">{hc.nsUnmatchedHoldCount}</span>
            </div>
            <div className="holds-recon-row">
              <span>NetSuite payment holds</span>
              <span className="holds-recon-val holds-recon-muted">0</span>
            </div>
            <button className="holds-recon-detail" onClick={() => setCompOpen(true)}>View full holds list →</button>
          </div>
        )}
      </>}
      <LaunchButton promptKey="supportHolds" label="Run Hold Audit →" data={data} />
      {compOpen && <HoldsComparisonPanel data={data} onClose={() => setCompOpen(false)} />}
    </div>
  );
}

function PlacementTile({ d, loading, data }) {
  const [taaOpen, setTaaOpen] = useState(false);
  const tc = data?.taaChecks;
  return (
    <div className="tile">
      <div className="tile-header">
        <span className="tile-label">TAA Placement Queue</span>
        <div className="tile-header-right">
          {!loading && d?.blockedCount > 0 && <span className="tile-badge tile-badge--warn">{d.blockedCount} blocked</span>}
          <SourceTag source="ns" />
        </div>
      </div>
      {loading ? <Skel h={70} /> : <>
        <div className="tile-hero-sm"><AnimatedCount value={d?.eligibleCount} /> <span className="tile-hero-unit">eligible</span></div>
        <div className="tile-sub">{fmt(d?.eligibleBalance)} ready for TAA</div>
        {tc && (
          <div className="taa-mini">
            <span className={tc.inactiveReps?.length > 0 ? "taa-mini-warn" : "taa-mini-ok"}>
              {tc.inactiveReps?.length > 0 ? `⚠ ${tc.inactiveReps.length} inactive rep${tc.inactiveReps.length > 1 ? "s" : ""}` : "✓ Reps active"}
            </span>
            <span className="taa-mini-sep">·</span>
            <span className={tc.withoutManagerCount > 0 ? "taa-mini-warn" : "taa-mini-ok"}>
              {tc.withManagerCount}/{tc.eligibleCount} have AM
            </span>
            <button className="taa-mini-btn" onClick={() => setTaaOpen(true)}>View checks →</button>
          </div>
        )}
      </>}
      <LaunchButton promptKey="placementQueue" label="Run Placement Tracker →" data={data} />
      {taaOpen && <TAAChecksPanel data={data} onClose={() => setTaaOpen(false)} />}
    </div>
  );
}

const LegalTile    = ({ d, loading, data }) => (
  <div className="tile tile--danger">
    <div className="tile-header"><span className="tile-label">Legal &amp; Blocked</span><SourceTag source="sf" /></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero"><AnimatedCount value={d?.count} /></div><div className="tile-sub">{fmt(d?.balance)} — litigation &amp; bankruptcy holds</div></>}
    <LaunchButton promptKey="legalBlocked" label="Run Legal Screen →" data={data} />
  </div>
);

const DemandTile = ({ d, loading, data }) => (
  <div className="tile">
    <div className="tile-header"><span className="tile-label">Demand Letter Queue</span><SourceTag source="ns" /></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero-sm"><AnimatedCount value={d?.count} /> <span className="tile-hero-unit">eligible</span></div><div className="tile-sub">{fmt(d?.balance)} — cleared for demand letters</div></>}
    <LaunchButton promptKey="demandLetterQueue" label="Draft Demand Letters →" data={data} />
  </div>
);

const ExtremeDPDTile = ({ d, loading, data }) => (
  <div className="tile tile--warn">
    <div className="tile-header"><span className="tile-label">Extreme DPD (365+)</span><div className="tile-header-right"><span className="tile-badge tile-badge--warn">Data review</span><SourceTag source="ns" /></div></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero"><AnimatedCount value={d?.count} /></div><div className="tile-sub">{fmt(d?.balance)} — verify before TAA submission</div></>}
    <LaunchButton promptKey="extremeDPD" label="Review Extreme DPD →" data={data} />
  </div>
);

const StopHoldTile = ({ d, loading, data }) => (
  <div className="tile">
    <div className="tile-header"><span className="tile-label">Stop Hold Overrides</span><SourceTag source="sf" /></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero"><AnimatedCount value={d?.count} /></div><div className="tile-sub">{fmt(d?.balance)} — reduced collections pressure</div></>}
    <LaunchButton promptKey="stopHoldOverrides" label="Run Payment Plan Risk →" data={data} />
  </div>
);

const StrategicTile = ({ d, loading, data }) => (
  <div className="tile">
    <div className="tile-header"><span className="tile-label">Strategic Account Watch</span><SourceTag source="sf" /></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero"><AnimatedCount value={d?.count} /></div><div className="tile-sub">{fmt(d?.balance)} — 30+ DPD, handle with care</div></>}
    <LaunchButton promptKey="strategicWatch" label="Review Strategic Accounts →" data={data} />
  </div>
);

const PendingHoldsTile = ({ d, loading, data }) => (
  <div className="tile">
    <div className="tile-header"><span className="tile-label">Possible Pending Holds</span><SourceTag source="sf" /></div>
    {loading ? <Skel h={50} /> : <><div className="tile-hero"><AnimatedCount value={d?.count} /></div><div className="tile-sub">{fmt(d?.balance)} — flagged, not yet actioned</div></>}
    <LaunchButton promptKey="possiblePendingHolds" label="Review Pending Holds →" data={data} />
  </div>
);

// ── App ───────────────────────────────────────────────────────────────
// ── Live Customer 360 drill-down modal (real-time NetSuite + Salesforce) ──
function CustomerModal({ drill, onClose }) {
  const d = drill.data;
  return (
    <div className="drill-overlay" onClick={onClose}>
      <div className="drill-panel" onClick={(e) => e.stopPropagation()}>
        <button className="drill-close" onClick={onClose}>×</button>
        <div className="drill-head">
          <div className="drill-name">{drill.name}</div>
          <span className="drill-live">● LIVE · NetSuite + Salesforce</span>
        </div>
        {drill.loading && <div className="drill-loading">Pulling live detail…</div>}
        {drill.error && <div className="drill-error">⚠ {drill.error}</div>}
        {d && (
          <>
            <div className="drill-stats">
              <div><span>Open balance</span><b>{fmt(d.total_usd)}</b></div>
              <div><span>Max DPD</span><b>{d.max_dpd}</b></div>
              <div><span>Open invoices</span><b>{d.invoice_count}</b></div>
            </div>
            {d.salesforce && !d.salesforce.error && (
              <div className="drill-sf">
                {d.salesforce.owner && <span className="drill-chip">Owner: {d.salesforce.owner}</span>}
                {(d.salesforce.holds || []).length > 0
                  ? d.salesforce.holds.map((h, i) => <span key={i} className="drill-chip drill-chip--hold">{h}</span>)
                  : <span className="drill-chip drill-chip--ok">No active holds</span>}
              </div>
            )}
            <div className="drill-table-wrap">
              <table className="drill-table">
                <thead><tr><th>Invoice</th><th>Amount</th><th>Invoice date</th><th>Due date</th><th>DPD</th></tr></thead>
                <tbody>
                  {d.invoices.map((iv, i) => (
                    <tr key={i}>
                      <td>{iv.invoice}</td>
                      <td className="num">
                        {fmt(iv.amount_usd)}
                        {iv.currency !== "USD" && (
                          <span className="fx-note" title={`Converted to USD from ${iv.currency}`}>
                            {iv.currency} {iv.amount_native.toLocaleString()} → USD
                          </span>
                        )}
                      </td>
                      <td>{iv.invoice_date}</td>
                      <td>{iv.due_date}</td>
                      <td className={`num${iv.dpd >= 90 ? " hot" : iv.dpd >= 60 ? " warn" : ""}`}>{iv.dpd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [deckBusy, setDeckBusy]       = useState(false);
  const [nsRefreshing, setNsRefreshing] = useState(false);
  const [drill, setDrill] = useState(null); // {loading, name, data, error}

  const openCustomer = useCallback(async (entityId, name) => {
    setDrill({ loading: true, name });
    try {
      const res = await fetch(`${API_BASE}/api/customer?entity=${encodeURIComponent(entityId)}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `Lookup failed (${res.status})`);
      setDrill({ loading: false, name: json.name || name, data: json });
    } catch (e) {
      setDrill({ loading: false, name, error: e.message });
    }
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const json = await res.json();
      setData(json); setLastRefresh(new Date());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  const generateDeck = useCallback(async () => {
    setDeckBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/pulse-deck`);
      if (!res.ok) {
        const msg = await res.json().catch(() => ({}));
        throw new Error(msg.error || `Build failed (${res.status})`);
      }
      const blob = await res.blob();
      const cd = res.headers.get("Content-Disposition") || "";
      const m = cd.match(/filename="?([^"]+)"?/);
      const baseName = (m ? decodeURIComponent(m[1]) : "AR Executive Pulse.pptx").replace(/\.pptx$/i, "");
      // Stamp each download with the generation time so the browser never collides
      // the filename (no more "(1)…(10)" pileup) and the newest file is obvious.
      const d = new Date();
      const stamp = `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, "0")}${String(d.getMinutes()).padStart(2, "0")}`;
      const name = `${baseName} [gen ${stamp}].pptx`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Could not generate the deck: " + e.message);
    } finally {
      setDeckBusy(false);
    }
  }, []);

  const refreshFromNetSuite = useCallback(async () => {
    setNsRefreshing(true);
    try {
      const res = await fetch(`${API_BASE}/api/refresh`, { method: "POST" });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || `Refresh failed (${res.status})`);
      await fetchData();
    } catch (e) {
      alert("NetSuite refresh failed: " + e.message);
    } finally {
      setNsRefreshing(false);
    }
  }, [fetchData]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const today = new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  const generatedAt = data?._generatedAt
    ? new Date(data._generatedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-wrap">
            <img src="https://d3j0t7vrtr92dk.cloudfront.net/advantive/1679332781_advantive-logo-full-color-rgb-1000px_300ppi.png" alt="Advantive" className="app-logo" />
          </div>
          <div className="header-divider" />
          <div className="header-title-block">
            <div className="app-title">AR Collections Dashboard</div>
            <div className="app-date">
              {today}
              {lastRefresh && <span className="app-refresh"> · {lastRefresh.toLocaleTimeString()}</span>}
              {generatedAt && <span className="app-snapshot"> · data from {generatedAt}</span>}
              {!loading && <RefreshCountdown seconds={REFRESH_SEC} onElapse={fetchData} />}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <div className="source-pill">
            <span className="source-dot" />
            <span className="source-text">NetSuite · Salesforce · Live</span>
          </div>
          <div className="header-divider" />
          <button className="refresh-btn primary" onClick={refreshFromNetSuite} disabled={nsRefreshing || loading}>
            {nsRefreshing ? "Pulling live data…" : "⟳ Refresh live data"}
          </button>
          <div className="header-divider" />
          <div className="header-actions-secondary">
            <button className="refresh-btn" onClick={generateDeck} disabled={deckBusy || loading}>{deckBusy ? "Building deck…" : "⬇ Pulse Deck"}</button>
            <a href={CHATGPT_URL} target="_blank" rel="noreferrer" className="open-agent-btn">Open Agent ↗</a>
          </div>
        </div>
      </header>

      <div className="app-body">
        {error && <div className="error-banner">⚠ Cannot reach API — {error}. Make sure the server is running.</div>}

        {/* Inactive rep alert */}
        {data && <InactiveRepBanner data={data} />}

        {/* Priorities */}
        <PrioritiesSection data={data} loading={loading} />

        {/* KPI Row */}
        <section>
          <SectionHeader title="Portfolio Overview" />
          <div className="kpi-row">
            <KPICard color="orange" label="Portfolio at Risk (60+ DPD)" source="ns"
              value={loading ? "—" : <AnimatedDollar value={data?.atRisk?.total} />}
              sub={loading ? "" : `${data?.atRisk?.accountCount || 0} accounts overdue`}
              topAccounts={data?.atRisk?.topAccounts} onDrill={openCustomer}
              promptKey="atRisk" launchLabel="Deep Dive →" data={data} />
            <KPICard color="red" label="Missing Support Holds" source="sf"
              value={loading ? "—" : <AnimatedCount value={data?.supportHolds?.missingHoldCount} />}
              sub={loading ? "" : `${fmt(data?.supportHolds?.missingHoldBalance)} unprotected · 45+ DPD`}
              promptKey="supportHolds" launchLabel="Run Hold Audit →" data={data} />
            <KPICard color="amber" label="TAA Placement Queue" source="ns"
              value={loading ? "—" : <AnimatedCount value={data?.placementQueue?.eligibleCount} />}
              sub={loading ? "" : `${fmt(data?.placementQueue?.eligibleBalance)} eligible · ${data?.placementQueue?.blockedCount || 0} blocked`}
              topAccounts={data?.placementQueue?.topAccounts} onDrill={openCustomer}
              promptKey="placementQueue" launchLabel="Run Placement Tracker →" data={data} />
            <KPICard color="blue" label="Write-Off Pool (180+ DPD)" source="ns"
              value={loading ? "—" : <AnimatedCount value={data?.writeOffPool?.candidateCount} />}
              sub={loading ? "" : `${fmt(data?.writeOffPool?.candidateBalance)} under review`}
              topAccounts={data?.writeOffPool?.topAccounts} onDrill={openCustomer}
              promptKey="writeOffPool" launchLabel="Run Write-Off Workflow →" data={data} />
          </div>
        </section>

        {/* Collections Team */}
        <section>
          <SectionHeader title="Collections Team" source="ns" sub="Click any rep to see their assigned accounts · Inactive reps and unassigned accounts require immediate attention" />
          <CollectionsTeamSection data={data} loading={loading} />
        </section>

        {/* Analytics: DPD + Holds */}
        <section>
          <SectionHeader title="AR Analytics" />
          <div className="analytics-row">
            <DPDTile d={data?.dpdBreakdown} loading={loading} data={data} />
            <HoldsTile d={data?.supportHolds} loading={loading} data={data} />
          </div>
        </section>

        {/* Action queues */}
        <section>
          <SectionHeader title="Action Queues" />
          <div className="tiles-grid tiles-grid--3">
            <DemandTile     d={data?.demandLetterQueue} loading={loading} data={data} />
            <LegalTile      d={data?.legalBlocked}      loading={loading} data={data} />
            <ExtremeDPDTile d={data?.extremeDPD}        loading={loading} data={data} />
          </div>
        </section>

        {/* Risk monitoring */}
        <section>
          <SectionHeader title="Risk Monitoring" source="sf" />
          <div className="tiles-grid tiles-grid--3">
            <StopHoldTile   d={data?.stopHoldOverrides} loading={loading} data={data} />
            <StrategicTile  d={data?.strategicWatch} loading={loading} data={data} />
            <PendingHoldsTile d={data?.possiblePendingHolds} loading={loading} data={data} />
          </div>
        </section>
      </div>

      {drill && <CustomerModal drill={drill} onClose={() => setDrill(null)} />}
    </div>
  );
}
