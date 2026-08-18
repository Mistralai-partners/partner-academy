# A2: Author and invoke a Skill · TASKS

- **Objective:** author a reusable Skill from a real recurring task and invoke it to produce a consistent, expected artifact.

- **Scenario (why this matters on the job):** you run the same formatting chore weekly. Capturing it once as a Skill means you, and your teammates, produce the identical shape every time without re-briefing.

- **Prerequisites:** signed in at chat.mistral.ai/work; access to the Skills area. Starter pack: `starter/raw-input.md`, `starter/second-input.md`, `starter/output-contract-card.md`, `starter/skill-skeleton.md`.

- **Done when:** the authored Skill appears in the Skills list and, on the *second, unseen* input, produces an artifact matching `starter/output-contract-card.md`.

## Steps (in-app)

- Open the Skills area and start a new Skill. `[VERIFY]` the exact create control label on screen.
- Author the Skill from `starter/skill-skeleton.md`: fill the name, a tightly scoped description or trigger, and instructions that carry the full output contract.
   - *Hint:* the failure to avoid is an over-broad trigger. Scope it to "raw meeting notes to weekly status update," not "summaries."
- Save the Skill and confirm it appears in the Skills list.
- Start a fresh conversation and invoke the Skill on `starter/raw-input.md`. Confirm the output has all six sections in order and the action-item table.
- Invoke the same Skill on `starter/second-input.md` with no extra prompting.
   - *Hint:* if the second output drifts (missing a section, no owner/due on an action), the contract is under-specified in the Skill. Tighten the instructions, do not re-prompt.

## Acceptance

Pass when the Skill runs on the second input and the artifact matches the contract (six sections in order, neutral business tone, action items as an Owner | Action | Due table with a value or "TBD" in every cell). See `VERIFY.md`. Compare against `solution/skill-definition.md` and `solution/expected-artifact.md`.

## Stretch

Share the Skill so a teammate invokes it, then compare the two outputs for drift.
