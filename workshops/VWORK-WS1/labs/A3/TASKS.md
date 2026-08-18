# A3: Connect and use · TASKS

- **Objective:** connect an external tool under a least-privilege scope and use the connected action inside a task.

- **Scenario (why this matters on the job):** real tasks need live inputs from your systems of record. Doing that safely means granting the minimum scope and confirming the *right* item came back.

- **Prerequisites:** signed in at chat.mistral.ai/work; one tool you can safely connect read-only (or the walkthrough). Starter pack: `starter/scenario-card.md`, `starter/connector-choice.md`, `starter/named-item-checklist.md`.

- **Done when:** a named real item from the connected tool is present in a task output, pulled under a read-only scope.

## Steps (in-app): primary path (Featured OAuth connector)

- Read `starter/connector-choice.md` and pick your tool.
- Fill `starter/named-item-checklist.md`: the exact item name or id and one fact you already know about it.
- Open Connectors and connect the tool with OAuth. Grant **read access only**; decline write/delete scopes you do not need. `[VERIFY]` the exact consent and per-function permission labels at capture.
- Confirm the tool shows connected with its per-function scope visible.
- In a task, ask Vibe Work to pull the **named** item (use the exact name, not a category). Approve the read action when prompted.
   - *Hint:* if it returns a generic answer with no named item, you asked for a category. Re-ask with the exact name or id.
- Confirm the specific item name or id, and your known fact, appear in the output.

## Steps (stretch): MCP connector

Wire a remote MCP server instead: enter its `/mcp` endpoint URL (Streamable HTTP) with OAuth or a Bearer token, scoped read-only, then pull the same class of item. Review the server's trust posture first. See `solution/mcp-config-example.md`. `[VERIFY]` the add-MCP-connector fields.

## Acceptance

Pass when the named item or id is present in the task output, pulled read-only. See `VERIFY.md`. Compare against `solution/reference-outcome.md`.

## Stretch

Do the MCP path and pull the same class of item through it.
