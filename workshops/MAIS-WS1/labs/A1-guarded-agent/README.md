# Activity A1: Build a Guarded Agent

## Scenario

You support a fintech ISV. The customer wants a support agent that looks up an order
status for shoppers. The agent must never reveal or process a full payment card number
and must never give financial advice. You build the agent, wire one tool, attach a
guardrail, then prove the guardrail blocks the disallowed request while the legitimate
order-status task still completes.

## The one behavior you build

An agent that completes the allowed task (order status) and refuses the disallowed task
(card handling and investment advice), with the guardrail attached at both the agent
level and the risky conversation call.

## Prerequisites

- Python 3.10 or later.
- `uv` installed.
- Your own `MISTRAL_API_KEY`. Put it in a `.env` file next to the scripts:
  `MISTRAL_API_KEY=sk-...`
- Setup takes under 5 minutes.

## Done when

Both acceptance checks pass and `verify.py` exits 0:

1. The allowed turn returns a tool-backed order-status answer.
2. The disallowed turn is blocked. No card digits are echoed. No advice is given.

## Quick start

Work in the `starter/` folder. Run the offline self-test first, then build, then verify.

```
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python build_agent.py --selftest
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python build_agent.py
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python verify.py
```

The reference answer is in `solution/`. Open it only after you attempt the tasks.

## What you learned

- How to register an agent with instructions, explicit completion args, and one tool.
- How to return a tool result so a turn is tool-backed.
- How a guardrail attaches at two layers, and why a guardrail that is defined but not
  attached fails silently.

## Next

This activity sits between MAIS-200 and MAIS-300. Next, move to MAIS-300 to add a
handoff to a specialist agent and confirm the guardrail holds across the handoff. See
the Stretch section in `TASKS.md` for a preview.
