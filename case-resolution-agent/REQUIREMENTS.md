# Support Case Agents — Requirements (from Jaime & Michelle)

Source: "Salesforce-GPT Integration & AI Agent Discussion" meeting, **2026-06-25** (Jaime
Rennick, Michelle Johnson, Zach Bergman, Tyler Stramback). This doc captures everything the
stakeholders asked for so the build covers all of it.

## ⛔ Blocker #1 — the Salesforce connector (do this BEFORE building anything live)

- The **ChatGPT ↔ Salesforce connector is not working** for the support team (~100–140 people).
  Today they **manually copy/paste** Salesforce data into ChatGPT.
- Even Jaime & Michelle hit a **"problem connecting Salesforce"** error in ChatGPT *despite*
  the green "approved by admin" check. Believed to be a Salesforce security issue supposedly
  fixed in the latest update — but it still errors.
- **Claude's** Salesforce connector **does** work, for the small handful who have Claude. (Zach
  prefers building on Claude, but few people have Enterprise Claude access.)
- **Step 1 (Jaime owns):** file a **Business Systems case** to enable the ChatGPT connector.
  Rollout order:
  1. The four of us first: **Jaime, Michelle, Mark, Rashtin** (so we can build/test)
  2. Then **all managers** (test, work out kinks)
  3. Then the **whole support team** + a formal **enablement session** on how to use the tools
- Jaime will share the **case number** once filed. Nothing live works until the connector is on.

## The three tools

### 1. 🔧 Resolution Summary GPT  *(Zach builds first, with **Rashtin**)*
- **Today's manual process:** techs copy **all case detail + the case feed** into a GPT; it
  builds a resolution in a **specific template format**; they paste it into the **Resolution
  tab** in Salesforce.
- **Wanted:** "Give me a case resolution for case #X" → the GPT **auto-pulls** the case fields
  **and the feed** from Salesforce → drafts the resolution **in their template** → tech reviews
  and pastes it back. (No write access yet → manual paste; eventual write-back is a future ask.)
- **Also (Mark's angle, see tool 3):** search **past closed cases for the same product** for a
  prior resolution to ground the draft.
- ⚠️ Need the **exact resolution-tab template** from Rashtin/Michelle — output must match it.

### 2. 📊 Case Analyzer / Sentiment GPT  *(Jaime helps with requirements)*
- Manager picks a **time window** — "all cases that closed yesterday / last week / last month."
- GPT reads **every** case in that window and scores sentiment **Positive / Neutral / Negative**.
- **Surfaces the negative ones + their case numbers** so a reviewer checks ~5 instead of ~50.
- Purpose: targeted QA — coach the team member, or escalate a real customer issue — **before** it
  shows up as a bad survey score (today that takes weeks, or never surfaces).
- Reviewer then takes those case numbers into the resolution/review GPT for the deep look.
- **Knowledge-article generation (candidate, from Rashtin 2026-06-26):** because the Analyzer
  works across batches of closed cases, it's the right place to spot recurring resolved issues and
  draft **Knowledge Base articles** from them (vs. the Resolution agent, which is per-live-case).
  Confirm exact scope with Rashtin/Tyler in the Monday rebuild.

### 3. 🔁 Mark's tool — historical resolution finder  *(discovery call with Mark planned)*
- Mark's current workaround: every couple weeks he **dumps closed-case history into smaller
  "bite-sized flat files"** and a GPT reads those (because his GPT can't read Salesforce live).
- A working connector **eliminates the download/save step** (the bulk of his manual work).
- Function: "Put this case number in, look at **all previous cases for this product**, and tell
  me if there's a resolution." → essentially the historical-search half of tool #1. Treated as a
  **variant of the case analyzer / resolution finder**; confirm exact scope on the discovery call.

## Cross-cutting constraints (apply to all three)

- **2,000-record limit** on Salesforce pulls (record/download limit, confirmed by Jaime). Searching
  *all* history will exceed it — must scope.
- **Scope by *support product*** (business-unit level — DDI, D1, CommSense, etc.; each unit can
  have multiple products). This refines searches and keeps volume manageable. Jaime floated
  "an agent per product"; consensus = scope/filter by support product rather than separate agents.
- **Performance:** "all of it" could take hours. Managers will want full history; likely need a
  **1–2 year cap** + product scoping as a practical default. Specific, narrow prompting matters.
- **Read-only:** no Salesforce **write** access for the GPTs → all paste-back is manual.
- **Foreign-language cases** must be handled (manager question, 2026-06-26) — read natively;
  output in English by default, customer-facing text in the customer's language.

## Ownership & next steps
- **Zach** → Resolution Summary GPT, with **Rashtin**.
- **Analyzer** → owner TBD among interns; **Jaime** helps define requirements.
- **Mark's tool** → discovery call with Mark (Zach/Tyler) to learn what he built, then fold in.
- Jaime to do intros to **Rashtin** and **Mark** once connector access is granted.
- Being in-office (Mark is "right next door") should speed iteration.

## Open items to confirm
- [ ] Connector enabled for the 4 of us (Business Systems case — Jaime).
- [ ] Exact **resolution-tab template** wording/structure (Rashtin/Michelle).
- [ ] Is the resolution **customer-facing or internal**? (Drives tone + what's safe to include.)
- [ ] Resolution-tab field **character limit** (keep drafts within it).
- [ ] What counts as the **"feed"** — CaseComments + EmailMessages + Chatter FeedItems?
- [ ] Exact **"support product"** field used for scoping (see salesforce-action.md).
- [ ] History cap (all / 2yr / 1yr) and the 2,000-record workaround approach.
- [ ] Platform: ChatGPT (pending connector fix) vs Claude (works now, limited seats).
