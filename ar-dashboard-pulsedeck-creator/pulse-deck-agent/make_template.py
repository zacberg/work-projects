"""
make_template.py — one-time: turn last week's actual Pulse deck into the
tokenized template (pulse_template.pptx).

Run-level replacement only: a literal is swapped ONLY inside a run that fully
contains it, so the run keeps its exact formatting. Anything that spans runs is
left untouched and reported, so nothing gets visually mangled.
"""
import sys, os
from pptx import Presentation

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ZachBergman\Downloads\AR Executive Pulse Week Ending 5.21.26 (1).pptx"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pulse_template.pptx")

# literal in the 5/21 deck  ->  token   (high-confidence, distinctive strings only)
MAP = [
    ("5/21/26", "{{WEEK_ENDING}}"),
    ("$8.8M", "{{CASH_MTD}}"),
    ("$26.2M", "{{CASH_QTD}}"),
    ("$2.84M", "{{BAL_60}}"),
    ("$1.40M", "{{BAL_90}}"),
    ("$292k", "{{COLL_60_WEEK}}"),
    ("$297k", "{{COLL_90_WEEK}}"),
    ("$2.97M", "{{AGING60_START}}"),
    ("$161k", "{{AGING60_ROLLED_IN}}"),
    ("$2.82M", "{{AGING60_ENDING}}"),
    ("$2.90M", "{{AGING60_TARGET}}"),
    ("$1.62M", "{{AGING90_START}}"),
    ("$84k", "{{AGING90_ROLLED_IN}}"),
    ("$2.28M", "{{AGING90_TARGET}}"),
    ("$561k", "{{SCORE_MAY_DAILY_AVG}}"),
    ("Hallmark - $434k", "{{TOP_MOVER_1}}"),
    ("Mpact Operations - $228k", "{{TOP_MOVER_2}}"),
    ("Crown Bakeries - $196k", "{{TOP_MOVER_3}}"),
    ("77 Accounts", "{{HOLDS_UNDER_THREAT}}"),
    ("300 Accounts", "{{HOLDS_ON_HOLD}}"),
    ("$9M", "{{HOLDS_RELATED_PAYMENTS}}"),
    ("72%", "{{CASH_MTD_PCT}}"),
    ("58%", "{{CASH_QTD_PCT}}"),
    ("47%", "{{SCORE_MAY_ATTAINMENT}}"),
    ("51%", "{{SCORE_Q2_ATTAINMENT}}"),
]

counts = {tok: 0 for _, tok in MAP}

def runs_of(prs):
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        yield r
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            for r in p.runs:
                                yield r

prs = Presentation(SRC)
# longest literals first so substrings don't pre-empt full strings
for literal, token in sorted(MAP, key=lambda kv: -len(kv[0])):
    for r in runs_of(prs):
        if literal in r.text:
            n = r.text.count(literal)
            r.text = r.text.replace(literal, token)
            counts[token] += n

prs.save(OUT)

print(f"Saved: {OUT}\n")
print("REPLACED (token: # of spots):")
missing = []
for literal, token in MAP:
    c = counts[token]
    flag = "" if c else "   <-- NOT FOUND (spans runs / formatted oddly) -> do manually"
    print(f"  {token:<26} <- '{literal}'   x{c}{flag}")
    if not c:
        missing.append((literal, token))

# verify tokens are present in the saved file
chk = Presentation(OUT)
total = sum(r.text.count("{{") for r in runs_of(chk))
print(f"\nTotal '{{{{' tokens in saved template: {total}")
if missing:
    print("\nLEFT FOR MANUAL REPLACE:", ", ".join(f"'{l}'->{t}" for l,t in missing))
