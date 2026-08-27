# A3: Reference Outcome

What success looks like. Your tool and item differ; the shape is the same.

## Featured OAuth connector (primary path)

- On the Connectors page, the chosen tool shows **connected**, with its **per-function permissions** visible and set to read-only. Confirm the permission labels there.
- In the task, you asked for one **named** item ("Summarize Q3-plan.pdf from my Drive and list its sections").
- Vibe prompted for approval on the **read** action; you approved it.
- The output contains the specific item: it names `Q3-plan.pdf` and lists sections that match the known fact you recorded in `../starter/named-item-checklist.md` (for example a "Budget" section).

Reference shape of the output:

```
Source: Q3-plan.pdf (Google Drive, read-only connector)
Summary: <two or three sentences drawn from the file>
Sections: 1) Overview  2) Budget  3) Timeline
```

## MCP connector (stretch path)

- The MCP server is connected at its `/mcp` endpoint over Streamable HTTP with an OAuth or Bearer token, scoped read-only.
- The same class of item is pulled through the MCP tool; the named item or id appears in the output.

## The proof

The connected action succeeded because a **specific, named** item from an external system (its title or id) is present in the task output, pulled under a read-only scope you granted deliberately. A generic answer with no named item is not a pass; that means the connector was not actually exercised.
