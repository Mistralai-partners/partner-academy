# A2: Reference Skill Definition (solution)

A complete, filled-in Skill. Your wording may differ; the scope must be tight and the instructions must carry the full output contract.

> `[VERIFY]` the literal field labels against the live Skills UI. The name / scope / instructions structure is the grounded concept; confirm on-screen labels at capture.

```
Name: Weekly Status Update from Notes

Description / trigger:
Use this Skill only when the user provides raw meeting notes and asks for a weekly
status update. Do not use it for general summaries, email drafting, or any other
document type.

Instructions:
Turn the provided raw meeting notes into a Weekly Status Update with EXACTLY these
sections, in this order:

1. Summary: one or two sentences on overall status.
2. Progress: bullets of what moved forward.
3. Blockers and risks: bullets; each names the owner and any deadline.
4. Decisions: bullets of what was decided.
5. Open questions: bullets of unresolved items needing a call.
6. Action items: a table with columns: Owner | Action | Due.

Tone: neutral, concise, business. Do not restate the raw notes verbatim.
Length: fits on one screen; single-line bullets where possible.

Rules:
- Every action item must have an owner and a due date. If the notes omit a due date,
 write "TBD".
- Do not invent facts that are not in the notes.
- Preserve names exactly as written in the notes.
```

## Precedence note

This Skill overrides account custom instructions for its job. If the account has a standing "always write in first person" instruction, this Skill's structured output contract still governs when the Skill fires.
