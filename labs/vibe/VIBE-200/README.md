<!-- course-ref -->
**Course:** Mistral Vibe for Code Intermediate (VIBE-200)

# VIBE-200 Lab - textkit

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> tool versions, and a troubleshooting table.

A small, working reference project for the everyday Vibe Code loop: explore, fix,
generate, review, and tune a real repo with the Vibe CLI. This is **working code
you read and run**, not a broken starter you repair. `textkit` is a tiny
string-helpers package; `app/casing.py` is the pattern every helper imitates.

The `.vibe/` folder is the point of the lab. Read it before you run anything:

- `app/.vibe/config.toml` - a fresh session opens on the read-only `plan` agent,
  and the `bash` tool must ask before it runs. Safe-by-default for a shared repo.
- `app/.vibe/agents/reviewer.toml` - a read-only review agent (read and search
  only, no write, no shell).
- `app/AGENTS.md` - the project conventions Vibe loads on every run (type hints,
  Google-style docstrings, tests for every helper, scoped edits).

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/vibe/VIBE-200/app
```

Set `MISTRAL_API_KEY` in your environment (or a `.env` in this folder) for the
live `vibe` steps. Already cloned the repo for another lab? Just `cd` into this
folder instead.

## Read it, run it, check it

```bash
# 1. Read the working helpers and the .vibe/ config (above), then run the suite:
python3 -m pytest -q                     # slugify + truncate are green

# 2. See the read-only reviewer in action (needs MISTRAL_API_KEY):
vibe --agent reviewer --trust -p "Review app/slugify.py against our conventions" --output text

# 3. Confirm the end state:
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the suite is green, the
reviewer is read-only, and the project defaults are set. A green result never
depends on a live model call.

## Now try it (optional)

Add a `titlecase` helper the way `app/casing.py` is shaped: hand it to an
edit-approving agent, keep the change scoped, and ship a test with it.

```bash
vibe --agent accept-edits --trust -p "Add app/titlecase.py with a titlecase(text) helper shaped like app/casing.py, plus tests/test_titlecase.py; change only those files" --max-turns 8 --output text
python3 -m pytest -q
```
