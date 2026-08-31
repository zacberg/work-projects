# Resolution Summary GPT — Salesforce query reference

> **NOTE (2026-06-26):** the GPT now uses ChatGPT's **built-in Salesforce connector**, so a custom
> OpenAPI Action is **not required**. Keep this file as (a) the authoritative **field/query
> reference** for what the connector should retrieve, and (b) a **fallback** if you ever switch to
> a custom Action. The SOQL/SOSL below documents the intended retrieval; the connector forms its
> own queries from the field/filter guidance in `instructions.md`.

Read-only access to the Salesforce `Case` object. **Field names below are confirmed from the
live production `Case` schema** (pulled 2026-06-26) unless marked "confirm."

## Endpoint 1 — get the target case + feed (SOQL `/services/data/vXX.0/query`)

```sql
SELECT CaseNumber, Subject, Description, Status, IsClosed, Priority, Type, Reason,
       Case_Category__c, Case_Sub_Reason__c,
       Product_Category__c, Product_Brands_Text__c, Other_Support_Product__c, Product_Page_Screen__c,
       Resolution_Summary__c, Engineering_Resolution__c, Engineering_Description__c,
       Engineering_Fixed_in_Version__c,
       Account.Name, Contact.Name, CreatedDate, ClosedDate,
       (SELECT CommentBody, CreatedDate, CreatedBy.Name FROM CaseComments ORDER BY CreatedDate DESC),
       (SELECT Subject, TextBody, Incoming, FromAddress, MessageDate FROM EmailMessages ORDER BY MessageDate DESC)
FROM Case
WHERE CaseNumber = :caseNumber
```
`CaseComments` + `EmailMessages` = the **feed** the techs rely on. *(Confirm with Rashtin if
Chatter `FeedItem` posts are also needed.)*

## Endpoint 2 — find prior resolutions, same product (SOSL `/services/data/vXX.0/search`)

```
FIND {term1 OR term2 OR term3} IN ALL FIELDS
RETURNING Case(CaseNumber, Subject, Resolution_Summary__c, Engineering_Resolution__c,
               Product_Category__c, ClosedDate
               WHERE IsClosed = true AND Product_Category__c = :product
               ORDER BY ClosedDate DESC
               LIMIT 20)
```
SOSL gives relevance-ranked full-text matching. The `Product_Category__c` filter is what keeps
the result set under the **2,000-record limit** — always scope by support product.

## Confirmed from the live schema (no longer guesses)
- **Resolution lives in custom fields:** `Resolution_Summary__c` (customer-facing, textarea) and
  `Engineering_Resolution__c` (label "Resolution", textarea). There is **no** standard resolution
  field. `Resolution_Summary_Reviewed__c` (bool) and `Resolution_Delivered_Date__c` also exist.
- **No `Product__c` lookup.** Product is captured via `Product_Category__c` (picklist),
  `Product_Brands_Text__c` (string), `Other_Support_Product__c`, `Product_Page_Screen__c`.
- **`IsClosed`** is the clean "closed" filter — Status has ~10 different `Closed - *` variants
  plus `Resolution Delivered`, `Deployed`, etc. Don't filter on a single Status value.
- Standard fields present: `CaseNumber`, `AccountId`→Account, `ContactId`→Contact, `OwnerId`,
  `CreatedDate`. Child relationships: `CaseComments`, `EmailMessages`, `CaseArticles`, `Feeds`.

## Still confirm with Rashtin / Michelle
- [ ] Which field is the **"support product"** they mean for scoping — `Product_Category__c`, or a
      different field (the term "support product" / business unit like DDI/D1/CommSense may map to
      `Product_Category__c` or to a brand field). Verify before locking the search filter.
- [ ] Exact **Resolution-tab template** format the draft must match.
- [ ] Whether **`Resolution Delivered`** status counts as "resolved" for the historical search.
- [ ] Default **history window** (1 vs 2 years) and the **2,000-record** workaround if a broader
      pull is ever needed.

## Auth & build order
- Reuse the **AR-dashboard Salesforce connected-app / OAuth** (authorization-code flow; see
  `ar-dashboard/RESUME.md`). Production org `advantive.my.salesforce.com`. Read scope only.
- ⚠️ **Org-wide connector must be fixed first** (Business Systems case — Jaime). Nothing live
  works until the ChatGPT↔Salesforce connector is enabled for the team.
- Build order: connector access → confirm fields/template above → write OpenAPI schema for the
  two endpoints → paste into GPT Actions → paste `instructions.md` → test on real closed cases
  (include a foreign-language one).
