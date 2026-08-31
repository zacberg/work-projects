# Tokenized template — finishing checklist

`pulse_template.pptx` was auto-generated from the 5/21/26 deck. Structure verified
identical to the original (11 slides, 31 images, 5 tables). 24 of 25 number-spots
were tokenized automatically.

## Manual replacements to finish (PowerPoint → Home → Replace)
| Find | Replace with |
|---|---|
| `Mpact Operations - $228k` | `{{TOP_MOVER_2}}` |
| `37` (DSO number, slide 2) | `{{DSO}}` |
| `$0` (write-offs, slide 10) | `{{AGING90_WRITEOFFS}}` |
| `Medium` (forecast confidence, slide 2) | `{{FORECAST_CONFIDENCE}}` |

(Do "37" carefully — only the Days Sales Outstanding cell on slide 2. Use Find Next,
not Replace All, if you're unsure.)

## Left as plain text on purpose (agent drafts these weekly — no token needed)
- Decisions / Updates (slide 2)
- Risks to Cash / Forecast (slide 2)
- Root-cause bullets + "what changed this week" (slide 7)
- Top-10 customer table next-action notes (slide 6) — filled by the script

## What the template does / doesn't cover
- ✅ All text/numbers → swapped via tokens by build_pulse.py.
- ⬜ Charts → images; re-exported from the Excel (cash) / external source (aging) and dropped in.
- ⬜ Top-10 table → filled by build_pulse.py from the Payments & Aging data.

## Verify
Open pulse_template.pptx and compare to Jordan's original — it should look identical
except the {{tokens}}. If anything shifted, keep the original as backup and re-run
make_template.py.
