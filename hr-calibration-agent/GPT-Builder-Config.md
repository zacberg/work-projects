# GPT Builder Configuration — HR Calibration Summary GPT

Everything you type into ChatGPT's **Create a GPT → Configure** tab.

## Name
**HR Calibration Summary Agent**

## Description
Turns Advantive performance-calibration transcripts into one polished, per-employee summary — commentary, score changes, and final tier — and saves drafts to SharePoint. Confidential; HR use only.

## Instructions
Paste the full contents of **GPT-Instructions.md** here. (It's written to fit the ~8,000-char limit.)

## Conversation starters
> Keep these short — they appear as clickable buttons, so Aaron never types or pastes the long version. The Instructions hold all the detail.
- `Create the employee summaries.`
- `Process the new transcript and update the summaries.`
- `Show me everything about <name> this cycle.`
- `Who was discussed but isn't in the census?`

## Knowledge (upload these files)
- `employee_summaries_data.json` — the accumulating master record (source of truth).
- `Format-Reference.md` — the exact Word-doc layout.
> Re-upload `employee_summaries_data.json` whenever the master record changes, so the GPT's baseline stays current. (Knowledge files are read-only snapshots — the live accumulating copy lives in SharePoint.)

## Capabilities
- ✅ **Code Interpreter & Data Analysis** — ON. Needed to read the census `.xlsx` and to generate `.docx` files.
- ✅ **Web Search** — optional; off is fine (no external lookups needed).
- ✅ **Canvas** — optional.
- ☐ **Image generation** — OFF (not needed).

## Connector
- Enable the **Microsoft / SharePoint** connector for this GPT and confirm it can reach the
  **production** site: `https://advantiveadmin.sharepoint.com/sites/PerformanceManagement`,
  specifically `Shared Documents/Calibration/` (Calibration Transcripts, Processed Transcripts,
  Employee Summaries, active census) plus the broader Performance Management library's manager
  folders. This replaced the old Prompt Pirates (AI-Interns) test site once testing moved to
  production-shaped data.

## Actions
- None required **if** the connector handles both read and write (your test confirmed write works).
- If you later want a dedicated write path independent of the connector, see `SharePoint-WriteBack-Action.md` for an optional Power Automate / Graph action.

## Sharing
- Share to the HR group only (Aaron Leong + anyone running the cycle). **Do not** publish org-wide or to the public — confidential performance data.
- In ChatGPT Enterprise: **Share → Only people with access / specific people**, not "Everyone at Advantive."

## Sensitivity note for the GPT's "About"
> CONFIDENTIAL. Generates draft HR calibration summaries from meeting transcripts. Output requires human review (Aaron Leong) before use. Do not share outputs outside the HR calibration process.
