# A4: Governance Posture Card (starter)

The posture you must implement and then prove.

## The rule

> **Read-only steps may run unattended. Every write or send is gated on human approval.**

This is the safe default for any automation that touches the outside world: the boring refresh happens on its own, but anything that leaves your control (a send, a post, a file write) stops for a human.

## The approval controls (what you will see at run time)

When a gated action is about to run, Vibe Work shows the tool call and its arguments with three options:

| Option | What it does |
|---|---|
| Allow once | Approves this single action |
| Always allow for this chat | Pre-authorizes this class of action for the rest of this chat (not global) |
| Reject | Blocks the action; it does not run and the model is told not to retry |

"Always allow for this chat" is scoped to the chat, not the account. There is no session-level setting that bypasses approval for sensitive actions.

## What you must demonstrate

1. The automation exists and can execute a run with read-only steps pre-authorized.
2. A deliberately disallowed **send** is **Rejected**, and you can see that no action ran.

## The failure to avoid

Pre-authorizing a send "so the schedule is useful" removes the human from the loop. If you catch yourself doing that, move the send back behind approval. That split, unattended refresh and gated send, is what you must be able to explain.
