# A4: Reference Automation

A filled-in automation that implements the posture. Your names and cadence differ; the split (read-only unattended, send gated) must match.

> Confirm the dialog fields and pre-authorize control against the live product. Frequency options and approval controls are grounded from the prior live capture.

## Scheduled task (reference)

```
Automation type: Scheduled task # public preview
Name: Weekly report refresh
What it does: Re-run the synthesis of the source material and update the summary
Frequency: weekly
Pre-authorized: read-only steps only (gather + synthesize)
Gated: any send / write / post held for approval each run
```

- The unattended run gathers and re-synthesizes. It does **not** send anything.
- Any notification is queued for a human to approve at run time.

## Studio workflow (alternative reference)

```
Workflow: Weekly report refresh
Unattended steps: gather latest source material; produce updated synthesis
Gated steps: draft + send the stakeholder heads-up (held for approval)
```

## Why this is correct

The refresh is boring and safe, so it runs on its own. The send leaves your control, so it stops for a human every time. That is the posture on `../starter/governance-posture-card.md`. Pre-authorizing the send would make the schedule "more useful" and remove the human from the loop, which is exactly the failure to avoid.
