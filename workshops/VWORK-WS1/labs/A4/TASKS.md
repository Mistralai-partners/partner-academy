# A4: Automate and govern · TASKS

- **Objective:** compose a durable automation that runs unattended inside an approval posture, and prove the posture blocks a disallowed send.

- **Scenario (why this matters on the job):** automation is only safe if the human stays in the loop on anything that leaves your control. You build the refresh and then prove the guardrail.

- **Prerequisites:** signed in at chat.mistral.ai/work; a safe test write destination (draft email or test channel). Starter pack: `starter/scenario-card.md`, `starter/governance-posture-card.md`, `starter/automation-skeleton.md`.

- **Done when:** (a) the automation exists and executes a run with read-only steps pre-authorized, and (b) a disallowed send is Rejected with no action run.

## Steps (in-app)

- Read `starter/governance-posture-card.md`: read-only may run unattended; every send is gated.
- Compose the automation from `starter/automation-skeleton.md`: a scheduled task (choose a frequency) or a Studio workflow. In the scheduled-task dialog, pre-authorize **read-only steps only**.
   - *Hint:* do not pre-authorize the send "to make it useful." That is the failure this lab exists to catch.
- Confirm the automation exists and can execute a run (or first / dry run).
- In a live session, ask Vibe to draft and **send** a heads-up message to your safe test destination.
- When the approval prompt appears, read the tool call and its arguments, then click **Reject**.
- Confirm the response reports the rejected permission and that nothing was sent.

## Acceptance

Pass when **both** hold: the automation runs (or first / dry run), and the disallowed send is Rejected with no action taken. See `VERIFY.md`. Compare against `solution/reference-automation.md` and `solution/expected-rejection.md`.

## Stretch

Compare a scheduled task vs a Studio workflow for this job and state when you would choose each.
