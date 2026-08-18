# A4: Automation Skeleton (starter)

Compose your durable automation from this skeleton. Fill every TODO. Keep read-only steps pre-authorized and every send gated.

> `[VERIFY]` the exact scheduled-task dialog fields, the pre-authorize-read-only control, and the Studio-workflow-in-Work path against the live product at capture. The frequency options (once / daily / weekly / monthly / yearly) and the approval controls are grounded from the prior live capture; the pre-authorize control's exact label is to be confirmed.

## Scheduled task (primary path)

```
Automation type: Scheduled task # public preview
Name: <TODO: e.g. "Weekly report refresh">
What it does: <TODO: one line, e.g. "re-run the synthesis of <source> and update the summary">
Frequency: <TODO: once | daily | weekly | monthly | yearly>
Pre-authorized: read-only steps ONLY # do NOT pre-authorize any send
Gated (needs approval each run): every write / send / post
```

## Studio workflow (alternative path)

If you prefer a workflow surfaced in Work, define the same split:

```
Workflow: <TODO: name>
Unattended steps: <TODO: read-only synthesis / gather steps>
Gated steps: <TODO: any send / write, held for approval>
```

`[VERIFY]` the Studio-workflow-in-Work entry point and step configuration.

## The guardrail test (run this live, do not automate it)

In a live session, after the automation exists, ask:

```
Draft a short heads-up message about the refreshed report and send it to
<my safe test destination>.
```

When the approval prompt appears:

1. Read the tool call and its arguments (confirm it is the send you expect).
2. Click **Reject**.
3. Confirm the response reports the rejected permission and that no message was sent.

See `../solution/reference-automation.md` and `../solution/expected-rejection.md`.
