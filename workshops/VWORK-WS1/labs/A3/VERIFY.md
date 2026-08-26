# A3: Connect and use · VERIFY

Self-checkable acceptance. No instructor required.

## Pass condition (all must hold)

- A tool is connected and shows a **read-only** scope (per-function permissions visible).
- You asked for one **named** item (exact name or id), not a category.
- The task output contains that **specific** item: its title or id appears, and the known fact you recorded matches.
- If you chose a write path instead, the write completed **only after approval**.

## How to check

- On the Connectors page, confirm the tool is connected and the scope is read-only. Check the per-function permission labels there.
- In the output, find the exact item name or id from `starter/named-item-checklist.md`. A generic summary with no named item is **not** a pass; it means the connector was not exercised.
- Confirm the known fact you recorded appears, proving the pull was real.
- Compare against `solution/reference-outcome.md`.

## Why this is the right check

- The evidence is that a real connected action succeeded under a scope you controlled, not that the model produced plausible text.
- A named item present in the output distinguishes an actual tool call from a hallucinated summary.
- Requiring read-only proves you granted least privilege.
