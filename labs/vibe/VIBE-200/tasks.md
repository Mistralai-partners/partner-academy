# VIBE-200 Lab - Mistral Vibe for Code Intermediate (everyday development)

**Tier:** L200 (Intermediate - Apply). **Behavior this lab grades:** run the
everyday coding jobs (explore, fix, generate, review, tune) as scoped,
reviewable, test-backed tasks with the Vibe CLI, and set up a project so Vibe's
output fits your team's conventions.

**Prereqs:** `vibe` CLI installed (`vibe --version` >= 2.24), `MISTRAL_API_KEY`
set, Python 3.11+. You should have finished VIBE-100 (get-running fluency).

**The project:** `textkit`, a tiny string-helpers package with a pattern file
(`app/casing.py`), one buggy helper, one missing helper, and an unfinished
`.vibe/` config. You will drive Vibe to bring it up to standard.

**How to work it:** work in `starter/`. Run `bash ../verify/check.sh starter`
any time. You are **done when it reports 4 passed, 0 failed**. Tasks 2-5 are the
machine-checked gates; Task 1 is a read-only CLI exercise you run and confirm by
eye. Reference solution: `solution/`.

**Trust note:** this repo ships a `.vibe/` folder, so Vibe loads its config only
from a trusted directory. In an interactive session, accept the trust prompt the
first time. For the non-interactive `-p` commands below, add `--trust` (grants
trust for that one run; see `vibe --help`).

---

## 1. Explore before you touch it (on-ramp, read-only)

- **Objective (Apply):** open unfamiliar code with zero change risk by choosing
  the read-only agent.
- **Scenario:** the first thing you do in a repo you did not write is understand
  it. The wrong agent here could edit files you only meant to read.
- Run from `starter/`:
  ```bash
  vibe --agent plan --trust -p "Summarize what app/slugify.py does and why tests/test_slugify.py fails" --output text
  ```
  Or start interactively with `vibe --agent plan`, then attach the file with
  `@`: `Read @app/slugify.py and explain the failure.`
- **Hint:** watch what the `plan` agent is *allowed* to do, not just what it
  says. It should never propose a write.
- **Acceptance:** the run makes no edits. Confirm nothing changed on disk
  (`git status` stays clean, or the files are byte-for-byte unchanged).

## 2. Fix the failing test with accept-edits *(machine-checked: gate 1)*

- **Objective (Apply):** delegate an everyday fix and verify it by running the
  suite, not by trusting the explanation.
- **Scenario:** `slugify` produces doubled and edge hyphens on some inputs. This
  is the bread-and-butter loop: let Vibe edit while you keep the test as the
  acceptance gate.
- Switch to the edit-approving agent and hand over the bug. Interactive:
  `vibe --agent accept-edits`, then `Fix @app/slugify.py so @tests/test_slugify.py passes.`
  Non-interactive equivalent:
  ```bash
  vibe --agent accept-edits --trust -p "Fix app/slugify.py so tests/test_slugify.py passes; change only that file" --max-turns 8 --output text
  ```
- **Hint:** the two tests name the exact inputs that break. Read the failure
  before you accept the diff; do not accept a diff that touches other files.
- **Acceptance:** `python3 -m pytest tests/test_slugify.py -q` is green (gate 1).

## 3. Generate a new helper that fits the project *(machine-checked: gate 2)*

- **Objective (Apply):** generate new code that matches project conventions by
  naming the outcome, referencing a pattern file, and stating constraints.
- **Scenario:** `tests/test_truncate.py` already specifies a helper that does not
  exist yet (`app/truncate.py::truncate_words`). On the job you generate to a
  spec and make it look like the rest of the codebase, not generic sample code.
- Reference the pattern file with `@` and constrain the request. Interactive:
  ```text
  Create app/truncate.py with a truncate_words(text, limit) function that makes
  @tests/test_truncate.py pass. Match the shape of @app/casing.py: type hints, a
  Google-style docstring, and an empty-input guard.
  ```
- **Hint:** the acceptance criteria are already written down in
  `tests/test_truncate.py`. The look-and-feel criteria are in `app/casing.py`.
- **Acceptance:** `python3 -m pytest tests/test_truncate.py -q` is green (gate 2).

## 4. Scope a read-only reviewer agent *(machine-checked: gate 3)*

- **Objective (Apply):** set least-privilege tool scope by reasoning about which
  tools a *reviewer* legitimately needs.
- **Scenario:** you want a reusable "review only" agent. As shipped,
  `.vibe/agents/reviewer.toml` still grants write and edit tools, so a review run
  could quietly modify the code it was asked to review. That is the blast-radius
  risk you are removing.
- Edit `.vibe/agents/reviewer.toml` so `enabled_tools` grants read and search
  only (no `write_file`, no `search_replace`, no `bash`). Then try it:
  ```bash
  vibe --agent reviewer --trust -p "Review app/slugify.py and list issues; do not change anything" --output text
  ```
- **Hint:** compare the tools listed in the starter file against what "read and
  reason about code" actually requires. Everything else is scope creep.
- **Acceptance:** verify gate 3 passes (`enabled_tools` set; none of the write or
  shell tools present).

## 5. Tune the project for better, safer results *(machine-checked: gate 4)*

- **Objective (Apply):** set project defaults in `.vibe/config.toml` and team
  conventions in `AGENTS.md` so Vibe's output fits the team by default.
- **Scenario:** a new contributor should not open the repo in an agent that can
  edit on the first keystroke, and Vibe should already know the house style
  without being told each time.
- Do two things:
  1. In `.vibe/config.toml`, set `default_agent` to a read-only-by-default agent
     and hold the `bash` tool to `permission = "ask"`.
  2. Create `AGENTS.md` at the repo root with the real conventions (pure
     functions with type hints and docstrings, an empty-input guard, a pytest
     test per helper, keep edits scoped). Match the `app/casing.py` shape.
- **Hint:** the CLI reads `default_agent` from `config.toml` and loads `AGENTS.md`
  from the (trusted) repo root. Both are grounded in the Configuration and Agents
  docs.
- **Acceptance:** verify gate 4 passes (`default_agent` set, `bash` permission is
  `ask`, and `AGENTS.md` states concrete conventions).

---

All flags above are from `vibe --help` (2.24.0): `-p/--prompt`, `--agent`
(`plan`, `accept-edits`, or a custom name), `--trust`, `--max-turns`,
`--output {text,json,streaming}`. File references with `@` and shell escapes are
interactive-mode features from the CLI docs.

## When you are done

`bash verify/check.sh starter` reports **4 passed, 0 failed**, and you have run
the plan-mode explore in Task 1. You have driven every everyday-dev lever the
course grades: read-only exploration, a test-backed fix, spec-and-pattern code
generation, least-privilege tool scoping, and project tuning with
`config.toml` + `AGENTS.md`. **Next:** VIBE-300 (Advanced) takes this into
tracing permission denials, defining sub-agents, and bounded headless automation.
