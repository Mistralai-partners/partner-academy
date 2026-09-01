# Vibe Config Quickstart

A minimal, end-to-end Mistral Vibe project that shows the recommended structure
and how **2 custom agents, 2 skills, and 2 instruction files** link together. It
is self-contained: clone this folder, set a key, and run it. A short narrated
walkthrough is in `dist/quickstart.mp4`; this README is the written version.

Grounded and verified against Vibe CLI **v2.24.3**.

## The mental model (read this first)

Vibe has three project-level building blocks, and they play different roles:

| Piece | Where | When it applies | Think of it as |
|---|---|---|---|
| **Instruction files** (`AGENTS.md`) | any directory | **Always on**. Injected automatically: the root at session start, a nested one the first time a file under it is read. Nearer-to-the-file wins. | Standing house rules |
| **Skills** (`.vibe/skills/<name>/SKILL.md`) | project or user | **On demand**. Only the name + description are always visible; the body loads when the task matches, or when you type `/<name>`. | A playbook you reach for |
| **Agents** (`.vibe/agents/<name>.toml`) | project or user | **When selected** with `--agent` (or `default_agent`). Bundles a prompt, a tool posture, and a safety level. | A named operator |

The wiring is `.vibe/config.toml` (`default_agent`, tool permissions). API keys
live in `.env`, never in config.

## What's in here

```
quickstart/
  AGENTS.md                     # instruction file #1: project-wide rules + which skill to use when
  src/AGENTS.md                 # instruction file #2: stricter rules for src/ (nearer-wins, lazy-injected)
  src/orders.py                 # clean example (docstrings + type hints)
  src/refunds.py                # the review target: breaks 2 conventions on purpose
  tests/test_orders.py          # the test-writer agent extends this
  .vibe/config.toml             # wiring: default_agent = "reviewer", tool posture
  .vibe/agents/reviewer.toml    # agent #1: read-only reviewer (safe)
  .vibe/agents/test-writer.toml # agent #2: can edit tests + run them (destructive)
  .vibe/prompts/reviewer.md     # reviewer's instructions (referenced by system_prompt_id)
  .vibe/prompts/test-writer.md  # test-writer's instructions
  .vibe/skills/security-checklist/  # skill #1: the review checklist (+ bundled checklist.md)
  .vibe/skills/changelog/           # skill #2: /changelog (+ bundled template.md)
  verify.py                     # offline check that the .vibe/ setup is well-formed
```

How the pieces reference each other (this is the point of the sample):
- The root **AGENTS.md** tells any agent: "when you review, use the `security-checklist` skill; to prepare a release, run `/changelog`."
- The **reviewer** agent's prompt loads the `security-checklist` skill and reports read-only.
- **src/AGENTS.md** adds a stricter docstring + type-hint + input-validation rule that wins inside `src/`.
- **config.toml** makes `reviewer` the default and sets the tool posture.

## Setup

```bash
cp .env.example .env      # then put your key in .env
# export MISTRAL_API_KEY=...   (or rely on the .env)
```

Uses `uv`. No other install step: `vibe` reads `.vibe/` automatically once the
folder is trusted (the commands below pass `--trust`).

## Do it

**1. Review with the read-only reviewer agent** (this is the default agent):

```bash
vibe --trust --agent reviewer -p "Review src/refunds.py. Apply the project conventions and the security checklist."
```

**2. Draft a changelog with skill #2.** `/changelog` runs `git` + `date`, so use
an agent that has the `bash` tool (the reviewer is read-only and cannot):

```bash
vibe --trust --agent test-writer -p "/changelog 0.1.0"
```

**3. Extend the tests with the test-writer agent** (it can edit `tests/` and run pytest):

```bash
vibe --trust --agent test-writer -p "Add tests for src/refunds.py, including a negative amount and an over-refund."
```

## Add it to your own project

The layout above is the whole convention. To adopt it in any repo, copy two
things into your project and place each file where Vibe looks for it:

```
your-project/
  AGENTS.md                     # project rules at the repo root - always on
  <subdir>/AGENTS.md            # optional stricter rules; the nearest one wins
  .vibe/
    config.toml                 # default_agent + tool posture (the wiring)
    agents/<name>.toml          # your agents (agent name = the file name)
    prompts/<id>.md             # an agent's system_prompt_id points here
    skills/<name>/SKILL.md      # your skills (support files sit beside SKILL.md)
```

**Where to start, and how to continue:**
1. **Copy** `.vibe/` and `AGENTS.md` from this sample into your repo root.
2. **Run it:** `vibe --trust --agent reviewer -p "review <a file in your repo>"` and watch it apply your rules + the skill.
3. **Make it yours:** edit `AGENTS.md` for your conventions, rename or add an agent under `.vibe/agents/` (with its prompt in `.vibe/prompts/`), add a skill under `.vibe/skills/<name>/`, then `/reload`.
4. **Go deeper:** VIBE-200 (Configuration & Customization) teaches each piece in its own hands-on lab.

## Verify your work

Offline structural check (no key, no network):

```bash
uv run python verify.py     # 13 checks: 2 agents, 2 skills, 2 AGENTS.md, config wiring
uv run --with pytest pytest -q
```

Real output from step 1 (captured live on v2.24.3) - note it cites `src/AGENTS.md`
(so the nested instruction file was in effect) and applies the checklist:

```
## Code Review: src/refunds.py

### High Severity
1. Missing input validation - src/refunds.py function calculate_refund
   No validation for negative order_total or amount_requested.
2. Missing docstring and type hints - violates strict src/AGENTS.md rule.

### Medium Severity
3. Silent cap instead of error - returns order_total when amount_requested > order_total
   rather than rejecting.

Summary: 2 High, 1 Medium. No secrets detected.
```

## Check your understanding
- Why did the reviewer know about the docstring rule without anyone loading it? (AGENTS.md is always-on.)
- Why can `test-writer` run `/changelog` but `reviewer` cannot? (Tool posture: only `test-writer` has `bash`.)
- Where does a custom agent's prompt text live? (`.vibe/prompts/<id>.md`, referenced by `system_prompt_id`; there is no inline prompt key.)

## Best practices and pitfalls (grounded on v2.24.3)
- **No inline `system_prompt`.** Agent instructions go in `.vibe/prompts/<id>.md`; the TOML sets `system_prompt_id`. An inline `system_prompt = "..."` is silently ignored.
- **No `[overrides]` table.** Override keys (`system_prompt_id`, `enabled_tools`, `[tools.*]`, ...) sit at the TOP LEVEL of the agent TOML.
- **Trusted folder.** Project `.vibe/` (agents, skills, AGENTS.md) only activates in a trusted folder. `--trust` (or `--add-dir`) makes it active non-interactively.
- **Tool names** are `read_file`, `write_file`, `edit`, `grep`, `bash`, `skill` (not `read`).
- **Agent vs subagent.** Only `agent_type = "agent"` is selectable with `--agent`.
- **An agent's tool posture gates its skills.** A skill that needs `bash` will not work under a read-only agent.
