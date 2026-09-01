<!-- course-ref -->
**Course:** Mistral Vibe for Code Advanced (VIBE-300)

# VIBE-300 Lab - advanced Vibe Code CLI

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`), pinned versions, and
> troubleshooting.

Working reference code for the advanced loop: choose the agent mode, scope tool
permissions, define a read-only sub-agent, trace a permission denial to its rule,
and run bounded headless automation. This is **working code you read and run**,
not a broken starter you repair.

Read the `.vibe/` setup before you run anything:

- `app/.vibe/config.toml` - the shell tool is scoped to `ask` (least privilege,
  not a blanket allow or a blanket deny).
- `app/.vibe/agents/reviewer.toml` - a read-only sub-agent (read and search only).
- `app/app/retry.py` - the helper with the working exponential backoff.

## Get the Lab Files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/vibe/VIBE-300/app
```

Set `MISTRAL_API_KEY` (or a `.env` in this folder) for the live `vibe` steps.
Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
python3 -m pytest -q          # retry suite is green (backoff is exponential)
python3 verify.py             # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the suite is green, the
shell tool is scoped to least privilege, and the reviewer sub-agent is read-only.
