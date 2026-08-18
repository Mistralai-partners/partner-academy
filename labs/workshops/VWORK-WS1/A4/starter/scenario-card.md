# A4: Scenario Card (starter)

You own a weekly report that must refresh on a cadence and notify stakeholders. The rule your organization insists on: nothing may be **sent** without a human in the loop. You will compose a durable automation that refreshes unattended, then prove the guardrail by making a disallowed send get blocked.

## Your task (two parts)

1. **Automate the refresh.** Compose a scheduled task (or a Studio workflow surfaced in Work) that re-runs a short synthesis unattended. Pre-authorize read-only steps only.
2. **Prove the guardrail.** In a live session, ask Vibe Work to draft and **send** a heads-up message to a safe test destination. When the approval prompt appears, **Reject** it, and confirm nothing ran.

## Safe test destination (pick one)

- A personal draft email that no real recipient receives.
- A private test channel you own.

Never approve a send to a real recipient during this activity. You will Reject first.

## Self-contained note

A4 needs only a safe test write destination. It uses no Library, Skill, connector, or output from another activity. See `governance-posture-card.md` for the rule and `automation-skeleton.md` for the build.
