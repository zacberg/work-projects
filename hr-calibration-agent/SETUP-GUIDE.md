# Build Guide — HR Calibration Summary GPT (ChatGPT Enterprise)

This is the ChatGPT port of the Claude/Cowork HR Calibration agent. Same job (transcripts → per-employee summaries), but **shareable** and able to **write back to SharePoint** — which the Claude M365 connector couldn't do.

## Files in this folder
| File | What it's for |
|------|---------------|
| `GPT-Instructions.md` | The system prompt → paste into the GPT's **Instructions** field. |
| `GPT-Builder-Config.md` | Name, description, starters, capabilities, knowledge, sharing. |
| `Format-Reference.md` | **Knowledge file** — exact Word-doc layout. |
| `employee_summaries_data.json` | **Knowledge file** — the accumulating master record. |
| `SharePoint-WriteBack-Action.md` | *Optional* dedicated write path (Power Automate / Graph), only if you ever need it. |

## Steps
1. **ChatGPT → Explore GPTs → Create** (or *My GPTs → Create a GPT*). Go to the **Configure** tab (skip the chat-based builder).
2. **Name + Description** — copy from `GPT-Builder-Config.md`.
3. **Instructions** — paste all of `GPT-Instructions.md`.
4. **Conversation starters** — add the four from the config file.
5. **Knowledge** — upload `Format-Reference.md` and `employee_summaries_data.json`.
6. **Capabilities** — turn **Code Interpreter & Data Analysis ON** (reads the `.xlsx` census, builds `.docx`). Image gen off.
7. **Connector** — enable the **Microsoft/SharePoint** connector and confirm it sees the **HR Calibration** folder under **Prompt Pirates**.
8. **Sharing** — share to the HR group only (Aaron Leong + cycle runners). Never org-wide/public.
9. **Test** (you've already confirmed write works) — run: *"List anyone in the transcripts who isn't in the employee census,"* then *"Process the Sales Engineers Calibration Session and save the updated docs."* Approve the write when prompted, then check the **Employee Summaries** folder.

## Keeping the master record current
The master `employee_summaries_data.json` accumulates over time. Two copies exist:
- **Live copy in SharePoint** (HR Calibration folder) — the GPT reads/updates this each run.
- **Knowledge-file snapshot** in the GPT — a static baseline.

After a cycle, **re-upload the updated JSON as the Knowledge file** so the GPT's baseline matches SharePoint. (Knowledge files don't auto-sync.)

## Guardrails baked in
- Output is always a **draft**; Aaron reviews before use.
- The GPT **asks for approval before writing** to SharePoint.
- It records only what the room decided — it never assigns its own scores.
- Anyone not in the census is **flagged**, not guessed.

## Carryover to resolve (from Jonrae's handoff)
- "Mayrav / Merab" and "Aiden" — Sales Engineering, mgr Lonnie Sneed — not in census.
- Several legacy records have manager "Unknown" — fill from census.

## How this differs from the Claude version
| | Claude / Cowork | ChatGPT Enterprise GPT |
|---|---|---|
| Read SharePoint | M365 connector (read-only) | SharePoint connector |
| Write to SharePoint | ❌ manual upload | ✅ confirmed working |
| Shareable as an agent | ❌ | ✅ share to HR group |
| Generate `.docx` | ✅ | ✅ (Code Interpreter) |
