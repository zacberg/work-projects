# Employee Summary — Format Reference

> Attach this as a **Knowledge** file. It defines the exact layout of every per-employee Word
> doc. Updated 2026-07-14 to match the current instructions: new filename convention, the
> three-way output destinations, and the FINAL SCORE SUMMARY block added with Kaitlyn.

## Filename

`calibration_[first initial + last name]_[manager full name].docx` — all lowercase, underscores
for spaces. Example: `calibration_jsmith_aaron_leong.docx`. If two employees would produce the
same filename, append `_2` to the second and flag it for HR review.

## Where each doc goes (all three, kept in sync)

1. `Shared Documents/Calibration/Employee Summaries/` — canonical copy.
2. The broader Performance Management "employee summaries" folder — all-employee copy.
3. That employee's actual manager's folder in the broader Performance Management library —
   manager-facing copy. Never file a person's own summary under a folder that exists for them
   as a manager; always their own manager's folder, even if they manage others.

## Document layout

**Header block:**
- Legal Name / Preferred Name / Manager / Department
- Current calibration period + transcript date range

**Body:**
- Summary of what was said (positive and negative themes) — no speaker attribution; quotes may
  appear but presented cleanly in the narrative, not as speaker-tagged lines.
- Score-change table:

| Dimension | From → To | Reason |
|-----------|-----------|--------|
| Performance | 0 → 4.0 | Data-entry error; corrected to reflect 115% quota. |
| Results Orientation | 5 → 4.0 | A 5 is the single company role model; not the right bar here. |

  - Reason must carry the transcript-backed rationale, not just "the score changed." Include a
    direct verbatim quote when the transcript has one that justifies the change; otherwise a
    faithful paraphrase with no quotation marks.
  - If a score wasn't stated, show `— → [value]` and store `null` in the JSON; mark it
    "Needs confirmation."
- Final tier/outcome, if stated.
- A short comparison note against the most recent prior confirmed state (or an explicit note
  that no prior record existed, or that only a baseline-score file was used for starting context).
- Confidential footer: `CONFIDENTIAL — HR Calibration — Draft for review`

**Last section — FINAL SCORE SUMMARY (always last, overwritten every run):**

```
FINAL SCORE SUMMARY
Employee: [Legal Name]
Last updated: [most recent session date, MM/DD/YYYY]

Dimension            | Current Score              | As of Session
Performance          | [value or Needs confirmation] | [session name]
Results Orientation  | [value or Needs confirmation] | [session name]

Overall Tier: [most recently stated tier, or Not yet decided]
```

- Include every dimension ever scored for this person (skip ones never mentioned for them).
- Current Score = the most recently decided value for that dimension across all updates, or
  "Needs confirmation" if never resolved to a final number.
- As of Session = the session where that value was last confirmed.
- Never recalculate or infer — only values the calibration room explicitly decided.

## Multi-session rule

A person discussed across multiple sessions in the same calibration period gets one continuously
updated document — never split into multiple files, never drop earlier sessions.

## Tone

Factual and neutral. You are transcribing the room's decisions, not evaluating the employee.
Never introduce a score, judgment, or recommendation that wasn't said in the meeting.
