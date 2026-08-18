# A2: Author and invoke a Skill · VERIFY

Self-checkable acceptance. No instructor required.

## Pass condition (all must hold)

- The authored Skill appears in the Skills list.
- Invoked on `starter/raw-input.md`, it produces the six sections in order: Summary, Progress, Blockers and risks, Decisions, Open questions, Action items (as a table).
- Invoked on the **second, unseen** input `starter/second-input.md` with no extra prompting, the output has the **same structure and shape**.
- Every action-item row has an Owner, an Action, and a Due (a value or "TBD"); no invented facts; names preserved as written.

## How to check

- Open the Skills list and confirm the Skill is saved.
- Run both inputs and lay the two outputs side by side. If both have the identical six-section structure and the same action-item table columns, the Skill encodes the contract.
- If the second output is missing a section or an owner/due, the contract is under-specified. Tighten the Skill instructions and re-run. Do not fix it with a one-off prompt; that defeats the purpose.
- Compare against `solution/skill-definition.md` and `solution/expected-artifact.md`.

## Why this is the right check

- The evidence is that the Skill reproduces the artifact on input it has never seen, from the saved definition alone.
- Matching on the second input, not the first, proves you encoded a reusable contract rather than fitting one example.
- That is the difference between a Skill and a lucky prompt.
