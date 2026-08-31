"""
build_pulse.py  —  AR Executive Pulse deck builder
===================================================
Deterministically assembles Jordan Duke's weekly "AR Executive Pulse" deck by
FILLING a fixed, tokenized template (pulse_template.pptx) — it never freehands
slides, so the deck is layout-identical every week. Only the data changes.

What it fills:
  • text/number tokens   {{TOKEN}}      -> data["tokens"]
  • the Top-10 table      (tbl_top10)    -> data["top10"]
  • the aging tables       are already tokenized (filled via tokens)
  • cash chart images     (chart_* shapes) -> images named in data["charts"]

What it deliberately LEAVES ALONE:
  • the 8 aging/risk charts (gt60_trend, gt90_trend, root_cause, total_ar_aging,
    upcoming_to_60, payments_against_60, payments_by_timing_pct/$). Their data
    lives in YayPay / Power BI, not the AR Tracker, so they can't be faithfully
    regenerated. They keep last week's image and are re-snipped manually until a
    YayPay/Power BI source is wired in. (Any chart NOT listed in data["charts"]
    is left untouched — that's how the split is enforced.)

Usage:
    python build_pulse.py pulse_data.json
    python build_pulse.py pulse_data.json --charts-dir _charts --out "deck.pptx"

Requires: python-pptx
"""
import sys, json, os, argparse
from pptx import Presentation
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "pulse_template.pptx")


# ──────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────
def _iter_shapes(prs):
    for slide in prs.slides:
        for shape in slide.shapes:
            yield shape


def _find_shape(prs, name):
    for shape in _iter_shapes(prs):
        if shape.name == name:
            return shape
    return None


# ──────────────────────────────────────────────────────────────────────
# 1. TEXT TOKENS — replace {{TOKEN}} anywhere, even when split across runs
# ──────────────────────────────────────────────────────────────────────
def replace_tokens(prs, mapping):
    """Replace every {{TOKEN}} in the deck. PowerPoint often splits a token
    across multiple runs, so we operate at the paragraph level: join the runs,
    substitute, then write the result back into the first run (keeping its
    formatting) and clear the rest. Returns the set of tokens actually used."""
    used = set()

    def fix_paragraph(p):
        full = "".join(r.text for r in p.runs)
        if "{{" not in full:
            return
        new = full
        for k, v in mapping.items():
            tok = "{{" + k + "}}"
            if tok in new:
                new = new.replace(tok, str(v))
                used.add(k)
        if new != full and p.runs:
            p.runs[0].text = new
            for r in p.runs[1:]:
                r.text = ""

    for shape in _iter_shapes(prs):
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                fix_paragraph(p)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    for p in cell.text_frame.paragraphs:
                        fix_paragraph(p)
    return used


def remaining_tokens(prs):
    """List any {{TOKEN}} still left unfilled (so the agent knows what's missing)."""
    import re
    left = set()
    for shape in _iter_shapes(prs):
        if shape.has_text_frame:
            left.update(re.findall(r"\{\{[A-Z0-9_]+\}\}", shape.text_frame.text))
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    left.update(re.findall(r"\{\{[A-Z0-9_]+\}\}", cell.text_frame.text))
    return sorted(left)


# ──────────────────────────────────────────────────────────────────────
# 2. TABLES — fill body rows of a named table
# ──────────────────────────────────────────────────────────────────────
def fill_table(prs, shape_name, rows, columns, keep_extra=True):
    """Fill a named table's body rows from `rows` (list of dicts). `columns` is
    the ordered list of dict keys mapping to table columns (col 0..n). Row 0 is
    the header and is left untouched. Writes cell text in-place so cell styling
    is preserved (writing .text replaces runs but keeps cell/para formatting)."""
    sh = _find_shape(prs, shape_name)
    if sh is None or not sh.has_table:
        print(f"  [warn] table '{shape_name}' not found — skipping")
        return
    table = sh.table
    body_rows = len(table.rows) - 1
    for i in range(1, len(table.rows)):
        rd = rows[i - 1] if i - 1 < len(rows) else None
        for c, key in enumerate(columns):
            if c >= len(table.columns):
                break
            if rd is not None:
                _set_cell_text(table.cell(i, c), str(rd.get(key, "")))
            elif not keep_extra:
                _set_cell_text(table.cell(i, c), "")
    if len(rows) > body_rows:
        print(f"  [note] {shape_name}: {len(rows)} rows given, only {body_rows} fit — extra ignored")


def _set_cell_text(cell, text):
    """Set a cell's text while keeping its first run's formatting."""
    tf = cell.text_frame
    p = tf.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run().text = text
    # clear any extra paragraphs
    for extra in tf.paragraphs[1:]:
        for r in extra.runs:
            r.text = ""


# ──────────────────────────────────────────────────────────────────────
# 3. CHART IMAGES — swap the bytes inside an existing picture (keeps geometry)
# ──────────────────────────────────────────────────────────────────────
def swap_chart_image(prs, shape_name, image_path):
    """Replace the image inside an existing picture (matched by name), keeping
    its exact size/position. Returns True on success."""
    pic = _find_shape(prs, shape_name)
    if pic is None:
        print(f"  [warn] chart shape '{shape_name}' not found — skipping")
        return False
    try:
        blip = pic._element.blipFill.blip
        rId = blip.get(qn("r:embed"))
        part = pic.part.related_part(rId)
        with open(image_path, "rb") as f:
            part._blob = f.read()
        return True
    except Exception as e:
        print(f"  [warn] chart '{shape_name}' swap failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
TOP10_COLUMNS = ["customer", "exposure", "status", "root_cause",
                 "owner", "timeline", "next_action"]


def build(data_path, charts_dir=None, out_path=None, template=TEMPLATE):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    charts_dir = charts_dir or os.path.join(HERE, "_charts")
    prs = Presentation(template)

    # 0. official cash/target numbers sourced from the AR Tracker (authoritative for
    #    the deck) — these override whatever the snapshot provided.
    ar_path = data.get("ar_tracker_path")
    if ar_path and os.path.exists(ar_path):
        try:
            from ar_tracker import read_scalar_tokens
            scalars = read_scalar_tokens(ar_path)
            if scalars:
                data.setdefault("tokens", {}).update(scalars)
                print(f"  AR Tracker scalars: {', '.join(sorted(scalars))}")
        except Exception as e:
            print(f"  [warn] AR Tracker scalar read failed: {e}")

    # 1. text / numbers
    used = replace_tokens(prs, data.get("tokens", {}))
    print(f"  tokens filled: {len(used)}")

    # 2. Top-10 table (clear unused rows — stale customers would be wrong)
    if data.get("top10"):
        fill_table(prs, "tbl_top10", data["top10"], TOP10_COLUMNS, keep_extra=False)
        print(f"  Top-10 rows filled: {min(len(data['top10']), 10)}")

    # 3. cash chart images (only those provided; aging charts left untouched)
    swapped = 0
    for shape_name, image_name in (data.get("charts") or {}).items():
        if shape_name.startswith("_"):   # skip _comment keys
            continue
        path = image_name if os.path.isabs(image_name) else os.path.join(charts_dir, image_name)
        if not os.path.exists(path):
            print(f"  [warn] chart image not found: {path} (for {shape_name})")
            continue
        if swap_chart_image(prs, shape_name, path):
            swapped += 1
    print(f"  charts swapped: {swapped}")

    # data-driven charts generated from live data (no AI, matplotlib)
    filled = set()
    aging = data.get("aging_buckets")
    if aging:
        try:
            from charts import render_total_ar_aging
            img = os.path.join(charts_dir, "gen_total_ar_aging.png")
            render_total_ar_aging(aging, img)
            for s in ("chart_total_ar_aging", "chart_total_ar_aging_2"):
                if swap_chart_image(prs, s, img):
                    filled.add(s)
            print(f"  generated total_ar_aging strip -> slides 4 & 10")
        except Exception as e:
            print(f"  [warn] aging strip generation failed: {e}")

    # charts regenerated from the AR Tracker workbook (cash charts, etc.)
    ar_path = data.get("ar_tracker_path")
    if ar_path and os.path.exists(ar_path):
        try:
            from ar_tracker import generate_cash_charts
            ar_filled = generate_cash_charts(prs, ar_path, charts_dir, swap_chart_image, _find_shape)
            filled |= ar_filled
            print(f"  AR Tracker charts: {len(ar_filled)} -> {', '.join(sorted(ar_filled))}")
        except Exception as e:
            print(f"  [warn] AR Tracker chart generation failed: {e}")
    elif ar_path:
        print(f"  [warn] AR Tracker not found at {ar_path}")

    # placeholder charts: replace not-yet-sourced charts with a clear "pending" tile
    placeholders = data.get("placeholder_charts")
    if placeholders:
        try:
            from charts import render_placeholder
            from pptx.util import Emu
            n = 0
            for shape_name, spec in placeholders.items():
                if shape_name in filled:
                    continue  # already has a real generated chart
                sh = _find_shape(prs, shape_name)
                if sh is None:
                    continue
                caption, _, source = str(spec).partition("|")
                img = os.path.join(charts_dir, f"ph_{shape_name}.png")
                render_placeholder(caption or shape_name, source or "source",
                                   Emu(sh.width).inches, Emu(sh.height).inches, img)
                if swap_chart_image(prs, shape_name, img):
                    n += 1
            print(f"  placeholder charts: {n}")
        except Exception as e:
            print(f"  [warn] placeholder charts failed: {e}")

    # ── Slide 5: replace the stale "likely to roll" SmartArt with live cards ──
    roll = data.get("roll_cards")
    if roll:
        try:
            from charts import render_account_cards
            from pptx.util import Emu
            cards = [{
                "name": r.get("name", ""),
                "amount": r.get("amount"),
                "note": (f"{r['dpd']} days past due — approaching >60" if r.get("dpd") is not None else ""),
                "status": "",
            } for r in roll]
            img = os.path.join(charts_dir, "gen_roll_cards.png")
            for slide in prs.slides:
                target = next((s for s in slide.shapes if s.name == "Diagram 1"), None)
                if target is None:
                    continue
                L, Tp, W, H = target.left, target.top, target.width, target.height
                render_account_cards(cards, img, w_in=Emu(W).inches,
                                     card_h_in=max(0.8, (Emu(H).inches - 0.5) / max(len(cards), 1)),
                                     gap_in=0.14)
                target._element.getparent().remove(target._element)  # drop stale SmartArt
                slide.shapes.add_picture(img, L, Tp, width=W, height=H)
                print(f"  slide 5: replaced SmartArt with {len(cards)} live roll cards")
                break
        except Exception as e:
            print(f"  [warn] roll cards failed: {e}")

    # report anything still unfilled
    left = remaining_tokens(prs)
    if left:
        print(f"  [needs input] {len(left)} token(s) still unfilled: {', '.join(left)}")

    # 4. save
    label = data.get("tokens", {}).get("WEEK_ENDING", "output")
    out = out_path or os.path.join(HERE, f"AR Executive Pulse Week Ending {label}.pptx")
    prs.save(out)
    print(f"\n[OK] built: {out}")
    return out, left


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the AR Executive Pulse deck from pulse_data.json")
    ap.add_argument("data", nargs="?", default=os.path.join(HERE, "pulse_data.json"),
                    help="path to pulse_data.json")
    ap.add_argument("--charts-dir", default=None, help="folder holding cash chart images")
    ap.add_argument("--out", default=None, help="output .pptx path")
    ap.add_argument("--template", default=TEMPLATE, help="template .pptx path")
    args = ap.parse_args()
    build(args.data, charts_dir=args.charts_dir, out_path=args.out, template=args.template)
