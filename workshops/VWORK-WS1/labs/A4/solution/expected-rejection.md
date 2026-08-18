# A4: Expected Rejection Outcome (solution)

What you should see when you Reject the disallowed send. These UI labels and the rejection message are grounded from the prior live capture of Vibe Work's approval flow.

## The approval prompt

When you ask Vibe Work to draft and send the heads-up message, it stops and shows the tool call and its arguments with three controls:

- **Allow once**
- **Always allow for this chat**
- **Reject**

For example, the tool call shown is a send/create action with the message body and destination as arguments. Read them before deciding.

## The rejected outcome

Click **Reject**. The expected result:

- The response reports the rejected permission, with wording such as: **"The user rejected permission to use this specific tool call."**
- **No message is sent.** No file is created. Nothing left your control.
- The run stops at that step rather than retrying.

## The proof (two parts)

1. The automation exists and executed a run (or a first / dry run) with read-only steps pre-authorized.
2. The deliberately disallowed send was **Rejected**, the rejected-permission outcome is visible, and no action ran.

Both together are the pass. Seeing an action *held* and then *blocked*, with nothing sent, is the felt evidence that approval is the design, not a limitation.
