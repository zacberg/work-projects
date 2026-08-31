"""
ar_tracker.py — read the AR Tracker workbook and turn its staging data into the
deck's charts (deterministic, matplotlib). Sourced from the
'Weekly Deck Slide - RunRates' tab.

generate_cash_charts(prs, xlsx_path, charts_dir, swap_fn, find_fn) generates each
chart it can and swaps it into the matching template shape; returns the set of
shape names it filled (so the builder won't placeholder them).
"""
import os
import datetime
import openpyxl
import charts


def _grid(path, sheet, maxr, maxc):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    g = [[None] * maxc for _ in range(maxr)]
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=maxr, max_col=maxc, values_only=True)):
        for j, v in enumerate(row):
            g[i][j] = v
    wb.close()
    return g


def _anchor(g, text):
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v is not None and str(v).strip() == text:
                return r, c
    return None, None


def read_runrates(path):
    """Returns {chart_key: data} from the RunRates staging tab."""
    g = _grid(path, "Weekly Deck Slide - RunRates", 131, 20)
    out = {}

    # payment methods: 'Payment Method' anchor, label/count down the two columns
    r, c = _anchor(g, "Payment Method")
    if r is not None:
        pm = []
        rr = r + 1
        while rr < len(g) and g[rr][c] not in (None, ""):
            pm.append((str(g[rr][c]), g[rr][c + 1] or 0))
            rr += 1
        if pm:
            out["payment_methods"] = pm

    # weekly cash run rate: 'Cash Run Rate Weekly Avg.' anchor, (quarter, weekly avg)
    r, c = _anchor(g, "Cash Run Rate Weekly Avg.")
    if r is not None:
        wr = []
        rr = r + 1
        while rr < len(g) and g[rr][c] not in (None, ""):
            q, v = g[rr][c], g[rr][c + 1]
            if v is not None:
                wr.append((str(q), float(v)))
            rr += 1
        if wr:
            out["weekly_run_rate"] = wr

    # total cash collected (single row, 3 year values)
    r, c = _anchor(g, "Total Cash Collected")
    if r is not None:
        yrs = ["2024", "2025", "2026"]
        tcc = [(yrs[i], g[r][c + 1 + i]) for i in range(3) if g[r][c + 1 + i] is not None]
        if tcc:
            out["total_cash_collected"] = tcc

    # quarterly average cash run rate (header years; Q rows; $ values)
    r, c = _anchor(g, "Cash Run Rate per Quarter")
    if r is not None:
        years = [g[r][c + 1], g[r][c + 2], g[r][c + 3]]
        rows = []
        rr = r + 1
        while rr < len(g) and g[rr][c] is not None and str(g[rr][c]).startswith("Q"):
            rows.append((str(g[rr][c]), [g[rr][c + 1], g[rr][c + 2], g[rr][c + 3]]))
            rr += 1
        if rows:
            out["quarterly_avg_runrate"] = {"years": [str(int(y)) for y in years if y], "rows": rows}

    # overall cash total per quarter (values already in $ millions)
    r, c = _anchor(g, "Overall Cash Total per Quarter")
    if r is not None:
        years = [g[r][c + 1], g[r][c + 2], g[r][c + 3]]
        rows = []
        rr = r + 1
        while rr < len(g) and g[rr][c] is not None and str(g[rr][c]).startswith("Q"):
            rows.append((str(g[rr][c]), [g[rr][c + 1], g[rr][c + 2], g[rr][c + 3]]))
            rr += 1
        if rows:
            out["quarterly_totals"] = {"years": [str(int(y)) for y in years if y], "rows": rows}

    return out


def _find(g, text, contains=False):
    t = text.lower()
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v is None:
                continue
            s = str(v).strip()
            if (t in s.lower()) if contains else (s == text):
                return r, c
    return None, None


def read_scalar_tokens(path):
    """Pull the handful of deck numbers we can source *unambiguously* from the AR
    Tracker (clearly-labeled cells only). Returns {TOKEN: value}. Anything without a
    clean, reliable anchor is deliberately omitted so it stays a soft placeholder
    rather than risking a wrong number on a CFO deck."""
    money = lambda v: f"${round(float(v)):,}"
    toks = {}

    # current-month tab (fallback to prior month): EOM Goal/Actual -> MTD cash + %
    now = datetime.date.today()
    for label in (now.strftime("%B %Y"),
                  (now.replace(day=1) - datetime.timedelta(days=1)).strftime("%B %Y")):
        try:
            g = _grid(path, label, 60, 16)
        except Exception:
            continue
        r, c = _find(g, "EOM Goal", contains=True)
        if r is not None:
            goal, actual = g[r][c + 1], g[r][c + 2]
            if isinstance(actual, (int, float)):
                toks["CASH_MTD"] = money(actual)
                if isinstance(goal, (int, float)) and goal:
                    toks["CASH_MTD_PCT"] = f"{round(actual / goal * 100)}%"
        break  # use the first month tab that exists

    # Daily Cash Email Send: ">60 Q2 Target" threshold (round figure, e.g. "$2.9M")
    try:
        gd = _grid(path, "Daily Cash Email Send", 40, 14)
        r, c = _find(gd, ">60 Q2 Target", contains=True)
        if r is not None and gd[r][c + 1]:
            s = str(gd[r][c + 1]).strip()
            toks["AGING60_TARGET"] = s if s.startswith("<") else f"<{s}"
    except Exception:
        pass

    return toks


def read_target_vs_actual(path, month_label):
    """Read a monthly tab's 'by Week' Goal/Actual block. Returns (weeks, total) or None."""
    try:
        g = _grid(path, month_label, 60, 12)
    except Exception:
        return None
    r, c = None, None
    for ri, row in enumerate(g):
        for ci, v in enumerate(row):
            if v is not None and "by Week" in str(v):
                r, c = ri, ci
                break
        if r is not None:
            break
    if r is None:
        return None
    weeks, total = [], None
    rr = r + 1
    while rr < len(g) and g[rr][c] is not None:
        lab = str(g[rr][c])
        goal, actual = g[rr][c + 1], g[rr][c + 2]
        if lab.lower().startswith("week"):
            if goal:  # skip empty future weeks
                weeks.append((lab.replace("Week", "Week "), goal, actual))
        elif "EOM" in lab:
            total = (goal, actual)
            break
        rr += 1
    if weeks and total:
        return weeks, total
    return None


# AR Tracker data key -> (template shape name, generator)
def generate_cash_charts(prs, xlsx_path, charts_dir, swap_fn, find_fn):
    data = read_runrates(xlsx_path)
    filled = set()

    def emit(shape_name, render):
        sh = find_fn(prs, shape_name)
        if sh is None:
            return
        from pptx.util import Emu
        img = os.path.join(charts_dir, f"gen_{shape_name}.png")
        render(img, Emu(sh.width).inches, Emu(sh.height).inches)
        if swap_fn(prs, shape_name, img):
            filled.add(shape_name)

    if "payment_methods" in data:
        emit("chart_payment_methods",
             lambda img, w, h: charts.render_payment_methods(data["payment_methods"], img, w, h))
    if "weekly_run_rate" in data:
        emit("chart_weekly_run_rate",
             lambda img, w, h: charts.render_run_rate(data["weekly_run_rate"],
                                                      "Weekly Cash Run Rate - Avg", img, w, h))
    if "total_cash_collected" in data:
        emit("chart_cash_s3_1",
             lambda img, w, h: charts.render_pie_years(data["total_cash_collected"],
                                                      "Total Cash Collected '24-'26", img, w, h))
    if "quarterly_avg_runrate" in data:
        d = data["quarterly_avg_runrate"]
        emit("chart_cash_s3_2",
             lambda img, w, h: charts.render_grouped_bars(d["years"], d["rows"],
                                                         "Quarterly Avg Cash Run Rate '24-'26", img, w, h, unit="dollars"))
    if "quarterly_totals" in data:
        d2 = data["quarterly_totals"]
        emit("chart_cash_s3_3",
             lambda img, w, h: charts.render_grouped_bars(d2["years"], d2["rows"],
                                                         "Quarterly Cash Totals '24-'26 (M)", img, w, h,
                                                         unit="millions", horizontal=True))

    # Cash: Target vs Actual (current month tab) -> slides 2 & 9
    now = datetime.date.today()
    month_label = now.strftime("%B %Y")          # e.g. "June 2026"
    tva = read_target_vs_actual(xlsx_path, month_label)
    if tva is None:                               # fall back to prior month
        prev = (now.replace(day=1) - datetime.timedelta(days=1))
        month_label = prev.strftime("%B %Y")
        tva = read_target_vs_actual(xlsx_path, month_label)
    if tva:
        weeks, total = tva
        title = f"{month_label.split()[0]} Cash: Target VS Actual"
        for shape in ("chart_cash_target_vs_actual", "chart_cash_target_vs_actual_2"):
            emit(shape, lambda img, w, h, _w=weeks, _t=total: charts.render_target_vs_actual(_w, _t, title, img, w, h))
    return filled
