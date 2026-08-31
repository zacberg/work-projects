"""
charts.py — matplotlib generators for the deck's data-driven charts.

Styled to match Jordan's example deck exactly (year colors, full-dollar labels,
trend lines, axes), so the only thing that changes week to week is the data.
Deterministic — no AI.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Match the deck's font so charts don't look like they came from a different tool.
# Falls back gracefully if Calibri isn't registered with matplotlib.
plt.rcParams["font.family"] = ["Calibri", "Segoe UI", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#102A43"
# year palette (matches Jordan's deck): 2024 purple, 2025 orange, 2026 navy
YEAR_COLORS = {"2024": "#8E3A93", "2025": "#E8743B", "2026": "#102A43"}
# payment-methods "ocean" palette: ACH, Check, Link to Pay, Credit Card
OCEAN = ["#102A43", "#1F6E8C", "#B5532A", "#E8A87C", "#3a8fd4", "#9DC3E6"]

_DOLLARS = FuncFormatter(lambda v, _: f"${v:,.0f}")


def _abbr(v):
    # Full dollar amount with thousands separators (no M/K abbreviation) per request:
    # e.g. $83,789,000 — never $83.7M.
    return f"${float(v or 0):,.0f}"


def _year_of(label):
    for yy, yr in (("'24", "2024"), ("'25", "2025"), ("'26", "2026")):
        if yy in label:
            return yr
    return None


# ──────────────────────────────────────────────────────────────────────
# Total AR aging strip (slides 4 & 10)  — colored card row
# ──────────────────────────────────────────────────────────────────────
BUCKET_ORDER = ["Current", "1-30", "31-60", "61-90", "91-120", "121-180", "181-365", "365+"]
FILL = {"Total AR": "#FFFFFF", "Current": "#E2EFDA", "1-30": "#FFF2CC", "31-60": "#FFE699",
        "61-90": "#FCE4D6", "91-120": "#F8CBAD", "121-180": "#F4B183", "181-365": "#E6B8B7",
        "365+": "#D99694", ">60": "#FFFFFF"}


def _money(v):
    # Full dollar amount with thousands separators (no M/K abbreviation) per request.
    return f"${float(v or 0):,.0f}"


def render_total_ar_aging(buckets, out_path, w_in=12.97, h_in=1.15):
    total = sum(buckets.get(b, 0) for b in BUCKET_ORDER)
    gt60 = sum(buckets.get(b, 0) for b in ["61-90", "91-120", "121-180", "181-365", "365+"])
    cards = [("Total AR", total, False)] + [(b, buckets.get(b, 0), True) for b in BUCKET_ORDER] + [(">60", gt60, True)]
    n = len(cards)
    fig, ax = plt.subplots(figsize=(13.0, 1.35), dpi=200)
    ax.set_xlim(0, n); ax.set_ylim(0, 1); ax.axis("off")
    pad = 0.06
    for i, (label, val, show_pct) in enumerate(cards):
        x = i + pad; w = 1 - 2 * pad
        ax.add_patch(FancyBboxPatch((x, 0.30), w, 0.66, boxstyle="round,pad=0.01,rounding_size=0.04",
                                    linewidth=1.1, edgecolor="#BFBFBF", facecolor=FILL.get(label, "#FFFFFF")))
        cx = x + w / 2
        ax.text(cx, 0.86, label, ha="center", va="center", fontsize=8, color="#595959")
        ax.text(cx, 0.55, _money(val),
                ha="center", va="center", fontsize=10.5 if label == "Total AR" else 9, fontweight="bold", color=NAVY)
        if show_pct and total:
            ax.text(cx, 0.12, f"{val/total*100:.1f}%", ha="center", va="center", fontsize=9, color="#404040")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.98, bottom=0.02)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Top Accounts — uniform stacked cards (replaces the uneven per-box autofit look)
# Every card is identical: same height, same fonts, same colors. A thin status
# stripe on the left color-codes the account; the header is always navy/white.
# ──────────────────────────────────────────────────────────────────────
# status -> left stripe color (uniform palette; extend as needed)
STATUS_COLORS = {
    "paid": "#2E7D32", "received": "#2E7D32", "current": "#2E7D32",
    "promised": "#1F6E8C", "committed": "#1F6E8C", "late": "#1F6E8C",
    "working": "#E8743B", "pending": "#E8743B", "follow-up": "#E8743B",
    "dispute": "#C0392B", "disputed": "#C0392B", "legal": "#C0392B", "risk": "#C0392B",
}


def _status_color(status):
    s = (status or "").strip().lower()
    for key, col in STATUS_COLORS.items():
        if key in s:
            return col
    return NAVY


def render_account_cards(accounts, out_path, w_in=12.6, card_h_in=0.92, gap_in=0.16):
    """Render top accounts as a vertical stack of uniform cards.
    `accounts` = list of dicts: {name, amount, note, status?}.
    Uniform typography/sizing throughout — no per-card autofit drift."""
    n = max(len(accounts), 1)
    fig_h = n * card_h_in + (n - 1) * gap_in + 0.1
    fig, ax = plt.subplots(figsize=(w_in, fig_h), dpi=200)
    ax.set_xlim(0, 1); ax.set_ylim(0, n); ax.axis("off")
    unit = 1.0  # one card per y-unit
    pad_y = gap_in / (card_h_in + gap_in)  # fraction of a unit used as the gap
    ch = 1 - pad_y                          # card height in y-units
    for i, acct in enumerate(accounts):
        # top card first
        y = n - (i + 1) + pad_y / 2
        name = str(acct.get("name", "")).strip()
        amount = acct.get("amount")
        note = str(acct.get("note", "")).strip()
        stripe = _status_color(acct.get("status"))
        # card body (white, light border)
        ax.add_patch(FancyBboxPatch((0.004, y), 0.992, ch,
                                    boxstyle="round,pad=0.002,rounding_size=0.02",
                                    linewidth=1.0, edgecolor="#D9D9D9", facecolor="#FFFFFF",
                                    mutation_aspect=1 / (w_in / fig_h)))
        # left status stripe
        ax.add_patch(plt.Rectangle((0.004, y), 0.012, ch, facecolor=stripe, edgecolor="none"))
        # header: "Customer  —  $amount"  (uniform navy/bold)
        amt = _money(amount) if amount is not None else ""
        header = f"{name}  —  {amt}" if amt else name
        ax.text(0.035, y + ch * 0.70, header, ha="left", va="center",
                fontsize=13, fontweight="bold", color=NAVY)
        # note (uniform, single style); wrapped to the card width
        if note:
            ax.text(0.035, y + ch * 0.30, note, ha="left", va="center",
                    fontsize=9, color="#404040", wrap=True)
    fig.subplots_adjust(left=0.004, right=0.996, top=0.998, bottom=0.002)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Weekly Cash Run Rate: Avg  — year-colored bars + full $ labels + trend line
# ──────────────────────────────────────────────────────────────────────
def render_run_rate(pairs, title, out_path, w_in=4.46, h_in=2.64):
    labels = [p[0] for p in pairs]
    vals = [p[1] for p in pairs]            # may contain None for future quarters
    x = np.arange(len(labels))
    colors = [YEAR_COLORS.get(_year_of(l), "#999999") for l in labels]
    fig, ax = plt.subplots(figsize=(max(w_in, 3.2), max(h_in, 2.0)), dpi=200)
    plotted = [(int(xi), v) for xi, v in zip(x, vals) if v is not None]
    ax.bar([p[0] for p in plotted], [p[1] for p in plotted],
           color=[colors[p[0]] for p in plotted], width=0.66)
    for xi, v in plotted:
        ax.text(xi, v, _abbr(v), ha="center", va="bottom", fontsize=6, fontweight="bold", color="#222")
    if len(plotted) >= 2:
        xs = [p[0] for p in plotted]; ys = [p[1] for p in plotted]
        fit = np.poly1d(np.polyfit(xs, ys, 1))
        ax.plot(x, fit(x), ls=":", color="#999999", lw=1.2)
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7, color="#666")
    ax.get_yaxis().set_visible(False)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.margins(y=0.22)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Payment Methods  — full pie, "label, count" outside + bottom legend
# ──────────────────────────────────────────────────────────────────────
def render_payment_methods(methods, out_path, w_in=3.0, h_in=2.75):
    labels = [m[0] for m in methods]; vals = [m[1] for m in methods]
    fig, ax = plt.subplots(figsize=(max(w_in, 2.6), max(h_in, 2.4)), dpi=200)
    wedges, _ = ax.pie(vals, colors=OCEAN[:len(vals)], startangle=90, counterclock=False,
                       labels=[f"{l}, {v:,}" for l, v in zip(labels, vals)], labeldistance=1.08,
                       textprops=dict(fontsize=7.5, color="#333333"),
                       wedgeprops=dict(edgecolor="white", linewidth=1))
    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.10),
              ncol=len(labels), frameon=False, fontsize=7.5)
    ax.set(aspect="equal")
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Total Cash Collected  — full pie, $ labels on wedges, year legend
# ──────────────────────────────────────────────────────────────────────
def render_pie_years(pairs, title, out_path, w_in=4.45, h_in=2.64):
    labels = [p[0] for p in pairs]; vals = [p[1] or 0 for p in pairs]
    total = sum(vals) or 1
    colors = [YEAR_COLORS.get(l, "#3a8fd4") for l in labels]
    fig, ax = plt.subplots(figsize=(max(w_in, 3.0), max(h_in, 2.0)), dpi=200)
    ax.pie(vals, colors=colors, startangle=90, counterclock=False,
           autopct=lambda p: _abbr(p / 100 * total),
           textprops=dict(color="white", fontsize=7, fontweight="bold"),
           wedgeprops=dict(edgecolor="white"))
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY, pad=8)
    ax.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.10), ncol=len(labels), frameon=False, fontsize=8)
    ax.set(aspect="equal")
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Grouped bars (Quarterly Avg Run Rate / Quarterly Cash Totals)
# ──────────────────────────────────────────────────────────────────────
def render_grouped_bars(years, rows, title, out_path, w_in=4.45, h_in=2.64, unit="dollars", horizontal=False):
    groups = [r[0] for r in rows]
    n_year = len(years)
    idx = np.arange(len(groups))
    bw = 0.8 / max(n_year, 1)
    fig, ax = plt.subplots(figsize=(max(w_in, 3.0), max(h_in, 2.0)), dpi=200)
    lbl = _abbr if unit == "dollars" else (lambda v: f"{v:.1f}")
    for j, yr in enumerate(years):
        vals = [(r[1][j] or 0) for r in rows]
        off = (j - (n_year - 1) / 2) * bw
        color = YEAR_COLORS.get(str(yr), "#3a8fd4")
        if horizontal:
            ax.barh(idx + off, vals, height=bw, color=color, label=str(yr))
            for i, v in enumerate(vals):
                if v: ax.text(v, idx[i] + off, " " + lbl(v), va="center", ha="left", fontsize=6.5, color="#404040")
        else:
            ax.bar(idx + off, vals, width=bw, color=color, label=str(yr))
            for i, v in enumerate(vals):
                if v: ax.text(idx[i] + off, v, lbl(v), va="bottom", ha="center", fontsize=6, color="#404040")
    ax.set_title(title, fontsize=11.5, fontweight="bold", color=NAVY, pad=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    if horizontal:
        ax.set_yticks(idx); ax.set_yticklabels(groups, fontsize=8, color="#666")
        ax.get_xaxis().set_visible(False); ax.spines["bottom"].set_visible(False)
    else:
        ax.set_xticks(idx); ax.set_xticklabels(groups, fontsize=8, color="#666")
        ax.get_yaxis().set_visible(False); ax.spines["bottom"].set_color("#DDDDDD")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=n_year, frameon=False, fontsize=7.5)
    ax.margins(y=0.24, x=0.05)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# Cash: Target vs Actual  — Target/Actual bars + % of Target line, both axes
# ──────────────────────────────────────────────────────────────────────
def render_target_vs_actual(weeks, total, title, out_path, w_in=7.9, h_in=2.4):
    labels = [w[0] for w in weeks] + ["TOTAL"]
    goals = [w[1] or 0 for w in weeks] + [total[0] or 0]
    actuals = [w[2] or 0 for w in weeks] + [total[1] or 0]
    pct = [(a / g * 100 if g else 0) for g, a in zip(goals, actuals)]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(max(w_in, 5.0), max(h_in, 2.2)), dpi=200)
    ax.bar(x - 0.2, goals, width=0.4, color=NAVY, label="Target")
    ax.bar(x + 0.2, actuals, width=0.4, color="#E8743B", label="Actual")
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY, pad=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8, color="#666")
    ax.yaxis.set_major_formatter(_DOLLARS); ax.tick_params(labelsize=6.5, colors="#999")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD"); ax.spines["bottom"].set_color("#DDDDDD")
    # subtle horizontal gridlines aid reading bar heights against the % line
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.8)
    ax2 = ax.twinx()
    ax2.plot(x, pct, color="#2E7D32", marker="o", linewidth=2, label="% of Target")
    ax2.set_ylim(0, max(130, (max(pct) if pct else 0) + 15))
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.tick_params(labelsize=7, colors="#2E7D32")
    for s in ("top", "left"):
        ax2.spines[s].set_visible(False)
    for xi, p in zip(x, pct):
        if p:
            ax2.text(xi, p + 4, f"{p:.0f}%", ha="center", fontsize=6.5, color="#2E7D32")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False, fontsize=7.5)
    ax.margins(y=0.15)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out_path


# ──────────────────────────────────────────────────────────────────────
def render_placeholder(caption, source, w_in, h_in, out_path):
    # Quiet, finished-looking panel (not a dashed "draft" box): soft off-white fill,
    # thin light border, the chart title, and a small muted source note.
    fig, ax = plt.subplots(figsize=(max(w_in, 1.4), max(h_in, 0.9)), dpi=150)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                boxstyle="round,pad=0.01,rounding_size=0.03",
                                facecolor="#FAFAFA", edgecolor="#E4E4E4", linewidth=1.0,
                                mutation_aspect=1 / max(w_in / h_in, 0.1)))
    ax.text(0.5, 0.56, caption, ha="center", va="center", fontsize=12, color="#6B6B6B", fontweight="bold")
    ax.text(0.5, 0.36, f"awaiting {source} data", ha="center", va="center", fontsize=8.5, color="#B0B0B0")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, facecolor="white"); plt.close(fig)
    return out_path


if __name__ == "__main__":
    demo = {"Current": 15381976.18, "1-30": 2644786.25, "31-60": 1129050.25, "61-90": 855934.59,
            "91-120": 398228.52, "121-180": 305516.01, "181-365": 303406.08, "365+": 69220.13}
    render_total_ar_aging(demo, "_inspect/test_total_ar_aging.png")
    print("ok")
