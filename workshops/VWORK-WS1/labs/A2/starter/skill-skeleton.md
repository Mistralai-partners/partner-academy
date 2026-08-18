# A2: Skill Skeleton (starter)

Author a Vibe Work Skill from this skeleton. A Skill is a saved, reusable instruction set: a **name**, a **description or trigger** that scopes when it applies, and the **instructions** that encode the output contract.

> `[VERIFY]` the exact field labels in the Skills authoring UI (for example whether the scoping field is called "description", "trigger", or "when to use") against the live product at capture time. The three-part structure below (name / scope / instructions) is the concept to author; confirm the literal labels on screen.

Fill every TODO. Keep the scope tight so the Skill fires only on this task, not on unrelated requests.

```
Name:
<TODO: a specific name, e.g. "Weekly Status Update from Notes">

Description / trigger (scope it tightly):
<TODO: one line that fires ONLY for this task, e.g. "Use when the user provides raw
meeting notes and asks for a weekly status update. Do not use for general
summaries or other document types.">

Instructions (encode the output contract from output-contract-card.md):
<TODO: state that the output MUST have exactly these sections in order:
1) Summary, 2) Progress, 3) Blockers and risks (each with owner + deadline),
4) Decisions, 5) Open questions, 6) Action items as a table (Owner | Action | Due).>
<TODO: tone = neutral, concise, business; length = fits one screen.>
<TODO: rules: every action item has owner + due (use "TBD" if missing);
do not invent facts; preserve names as written.>
```

## Common defect to avoid

An over-broad description ("use for summaries") makes the Skill fire on unrelated requests. Scope it to "raw meeting notes to weekly status update" so it does not hijack other conversations.
