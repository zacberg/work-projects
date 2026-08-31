# OPTIONAL — Dedicated SharePoint Write-Back Action

You confirmed write-back already works through your connector, so **you probably don't need this.** Keep it only as a fallback if you ever want a write path that's independent of the connector (e.g., the connector loses write permission, or you want a Word-template-driven layout enforced server-side).

The cleanest no-Azure option in an M365 shop is **Power Automate**.

## Option A — Power Automate HTTP-trigger flow (recommended fallback)
**Flow:**
1. Trigger: **When an HTTP request is received** (generates a POST URL).
2. Action: **Populate a Microsoft Word template** (a `.docx` template in the HR Calibration folder with content controls for header + a repeating section for sessions).
3. Action: **Create file** → SharePoint → site *Prompt Pirates*, folder `HR Calibration/Employee Summaries`, name = `fileName`, content = output of step 2.
4. Respond to the GPT with `{ "status": "saved", "url": "<web url>" }`.

**Request schema the flow expects (and the GPT sends):**
```json
{
  "fileName": "Sella, Anthony.docx",
  "employee": { "legal_name": "...", "preferred_name": "...", "manager": "...", "department": "..." },
  "sessions": [ { "session": "...", "date": "...", "comments": ["..."],
    "score_changes": [ { "dimension": "...", "from": null, "to": 4.5, "reason": "..." } ],
    "final_tier": "..." } ]
}
```

**GPT Action OpenAPI (paste into the GPT's Actions → Schema):**
```yaml
openapi: 3.1.0
info:
  title: HR Calibration SharePoint Writer
  version: "1.0"
servers:
  - url: https://prod-XX.westus.logic.azure.com   # your flow's host
paths:
  /save:                                           # path + ?api-version&sig from the flow URL
    post:
      operationId: save_employee_summary
      summary: Save one employee calibration summary to SharePoint.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [fileName, employee, sessions]
              properties:
                fileName: { type: string }
                employee:
                  type: object
                  properties:
                    legal_name: { type: string }
                    preferred_name: { type: string }
                    manager: { type: string }
                    department: { type: string }
                sessions:
                  type: array
                  items:
                    type: object
                    properties:
                      session: { type: string }
                      date: { type: string }
                      comments: { type: array, items: { type: string } }
                      score_changes:
                        type: array
                        items:
                          type: object
                          properties:
                            dimension: { type: string }
                            from: { type: [number, "null"] }
                            to: { type: [number, "null"] }
                            reason: { type: string }
                      final_tier: { type: string }
      responses:
        "200":
          description: Saved
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string }
                  url: { type: string }
```
**Auth:** the Power Automate URL carries its own SAS signature, so set the Action's auth to **None** — but then treat the URL as a secret (don't share the GPT publicly). For tighter control, put the flow behind **API key** auth and add an `x-api-key` header check as the first flow step.

## Option B — Microsoft Graph (more setup)
Register an app in **Entra ID**, grant `Sites.ReadWrite.All` (or `Files.ReadWrite.All`), use OAuth2 auth-code flow in the Action, and `PUT /sites/{site-id}/drive/root:/HR Calibration/Employee Summaries/{fileName}:/content`. More moving parts and binary-upload limitations — only worth it if Power Automate isn't available.
