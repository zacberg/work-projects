# HR Calibration Summary Agent

An AI agent that turns Advantive's performance-calibration meeting transcripts into polished, per-employee draft summaries — capturing what was said, the score changes the calibration room discussed and decided, the final tier, and how each employee's record progresses across calibration cycles. Built on **ChatGPT Enterprise** with the Microsoft SharePoint connector; output is one Word doc per employee, written back to SharePoint for HR review.

> **Calibration cadence:** runs approximately three times per year. Each cycle, new transcripts are added (old ones are kept), the agent processes only the new batch, and extends each employee's history.

---

## Credits and Project History

**Built by [Jonrae Small](mailto:jonrae.small@advantive.com) and [Zach Bergman](mailto:zach.bergman@advantive.com)** — joint authors, equal credit.

Jonrae Small started the project and built the original HR Calibration agent: the concept, the extraction approach, the per-employee Word-doc format, the employee-census name-matching, and the first full run (50 employee summaries) as a **Claude / Cowork + Microsoft 365** workflow. Zach Bergman built the **ChatGPT Enterprise** version on that foundation, adding cross-cycle accumulation, SharePoint write-back, the live-census control model, and continuable multi-cycle runs.

Both contributed substantially; this is a collaborative project across two platforms. See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full breakdown.

| Stage | Platform | Author |
|-------|----------|--------|
| Original agent + first full run | Claude / Cowork + M365 | **Jonrae Small** |
| ChatGPT Enterprise version (this repo) | ChatGPT + SharePoint | **Zach Bergman** |

**Process owner:** Aaron Leong (HR) · **Calibration facilitator:** Suketa Shah

---

## Confidential Data — Not Stored in This Repository

This agent processes **confidential employee performance data**. None of that data lives in this repository:

- The employee census, calibration transcripts, and generated employee summaries live **only in SharePoint** (Prompt Pirates → HR Calibration), never in git.
- `employee_summaries_data.json` (the live structured record) and any `*.docx` summaries are **git-ignored**. A sanitized `employee_summaries_data.sample.json` is included to show the schema only.
- Do not commit real names, scores, tiers, or transcript content. Ever.

---

## What's in this repo

| File | Purpose |
|------|---------|
| `GPT-Instructions.md` | The system prompt pasted into the ChatGPT GPT builder (source of truth). |
| `GPT-Builder-Config.md` | Name, description, conversation starters, capabilities, sharing settings. |
| `Format-Reference.md` | The exact Word-doc layout — uploaded as a GPT Knowledge file. |
| `SETUP-GUIDE.md` | Step-by-step build instructions for the GPT. |
| `SharePoint-WriteBack-Action.md` | Optional fallback write path (Power Automate / Graph). |
| `employee_summaries_data.sample.json` | **Schema example only** — sanitized, no real data. |

## How it works (short version)

1. Aaron uploads the latest census file + the new cycle's transcripts to SharePoint.
2. He opens the GPT and clicks **"Create the employee summaries."**
3. The agent reads the newest census, matches everyone discussed, extracts commentary + decided score changes + final tier, and writes one Word doc per employee into that cycle's folder — plus a comparison note against the prior cycle.

Full details in `GPT-Instructions.md` and `SETUP-GUIDE.md`.

## Status

In testing. The agent has been validated against the January 2026 calibration transcript set and produced summaries for 50 employees. Multi-cycle testing is pending receipt of the remaining transcript files from the HR team.

---

_Last updated: 2026-07-20_
