"""
app.py — Pulse Deck Builder service
===================================
The external builder n8n calls (n8n Cloud can't run python-pptx itself).

POST /build
  multipart/form-data:
    data    : the pulse_data JSON (string)               [required]
    charts  : zero or more cash-chart image files.        [optional]
              Each file's *field name* must equal the template chart shape
              (e.g. "chart_weekly_run_rate"); its filename is ignored.
  -> returns the finished .pptx as a download.

GET /health -> {"ok": true}

Run locally:
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8000
"""
import os, json, tempfile, datetime
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_pulse  # reuse the exact same builder used locally

app = FastAPI(title="AR Pulse Deck Builder")

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.environ.get("PULSE_TEMPLATE",
                          os.path.join(os.path.dirname(HERE), "pulse_template.pptx"))


@app.get("/health")
def health():
    return {"ok": True, "template_exists": os.path.exists(TEMPLATE)}


@app.post("/build")
async def build_deck(data: str = Form(...), charts: list[UploadFile] = File(default=[])):
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"`data` is not valid JSON: {e}")

    work = tempfile.mkdtemp(prefix="pulse_")
    charts_dir = os.path.join(work, "_charts")
    os.makedirs(charts_dir, exist_ok=True)

    # Each uploaded file is named after its template chart shape, e.g.
    # "chart_weekly_run_rate.png". The filename STEM is the shape to swap.
    # Aging charts are simply not uploaded, so they're left untouched.
    chart_map = {k: v for k, v in (payload.get("charts") or {}).items()
                 if not k.startswith("_")}
    for up in charts:
        stem = os.path.splitext(os.path.basename(up.filename or ""))[0]
        if not stem:
            continue
        fname = f"{stem}.png"
        with open(os.path.join(charts_dir, fname), "wb") as f:
            f.write(await up.read())
        chart_map[stem] = fname
    payload["charts"] = chart_map

    data_path = os.path.join(work, "pulse_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    label = (payload.get("tokens") or {}).get("WEEK_ENDING", "output")
    out_path = os.path.join(work, f"AR Executive Pulse Week Ending {label}.pptx")
    try:
        build_pulse.build(data_path, charts_dir=charts_dir, out_path=out_path, template=TEMPLATE)
    except Exception as e:
        raise HTTPException(500, f"build failed: {e}")

    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=os.path.basename(out_path),
    )
