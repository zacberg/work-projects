# Contributors

This project was built by two authors, **with equal credit**. Jonrae Small started it and built the original agent; Zach Bergman built the ChatGPT version on that foundation. Both contributed substantially.

## Authors

**Jonrae Small** — jonrae.small@advantive.com

Started the project and built the original HR Calibration agent. Originated the concept and the entire approach: reading calibration transcripts, cross-referencing the employee census for preferred names and aliases, extracting per-employee commentary and decided score changes, and generating one Word document per employee. Built the original working version as a Claude / Cowork + Microsoft 365 workflow and completed the first full run (50 employee summaries).

**Zach Bergman** — zach.bergman@advantive.com

Built the ChatGPT Enterprise version of the agent (this repository) on Jonrae's foundation. Ported it to ChatGPT with the SharePoint connector and added: cross-cycle accumulation, write-back to SharePoint, the live-census-as-control model, dynamic per-cycle output, and continuable multi-cycle runs.

## Stakeholders

- **Aaron Leong** — HR; process owner and primary user of the output.
- **Suketa Shah** — facilitator of the calibration sessions.
