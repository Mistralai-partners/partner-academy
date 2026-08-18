# VIBE-300 Lab — Advanced Vibe Code CLI (hands-on)

**Tier:** L300 (Advanced — Analyze). **Behavior this lab grades:** drive,
scope, and *debug* an advanced Vibe Code CLI run — choose the agent mode, scope
tool permissions, define a sub-agent, trace a permission denial to its rule, and
run bounded headless automation.

**Prereqs:** `vibe` CLI installed (`vibe --version` ≥ 2.24), `MISTRAL_API_KEY`
set, Python 3.11+.

**How to work it:** work in `starter/`. Run `bash ../verify/check.sh starter`
any time. You are **done when it reports 3 passed, 0 failed** (Tasks 2, 3, and 4
are the machine-checked gates; Tasks 1, 5, and 6 are CLI exercises you run and
confirm by eye). Reference: `solution/`.

---

1. **Explore in plan mode (read-only).**
   - *Objective (Analyze):* understand unfamiliar code with zero change risk by
     picking the read-only agent mode.
   - *Why it matters:* on the job you inspect a repo before you touch it — the
     wrong mode here can edit files you only meant to read.
   - From `starter/`, run:
     `vibe --agent plan -p "Summarize what app/retry.py does and why test_retry.py fails" --output text`
   - *Acceptance:* the `plan` agent does not edit files — confirm `git status`
     stays clean.
2. **Fix the failing test (accept-edits / build).** *(machine-checked: check 1)*
   - *Objective (Apply/Analyze):* delegate a real fix and verify it, not just
     accept the diff.
   - *Why it matters:* letting the agent edit while you keep the test as the
     acceptance gate is the everyday advanced loop.
   - Let Vibe fix the exponential-backoff bug:
     `vibe -p "Fix app/retry.py so test_retry.py passes; make backoff exponential" --enabled-tools "read_file" --enabled-tools "edit_file" --enabled-tools "bash" --max-turns 6`
   - *Acceptance:* `python -m pytest -q` is green.
3. **Define a read-only sub-agent.** *(machine-checked: check 3)*
   - *Objective (Analyze):* scope a delegated agent to least privilege by
     reasoning about which tools a *reviewer* legitimately needs.
   - *Why it matters:* a sub-agent with write/bash access is a blast-radius risk;
     a reviewer should read and search only.
   - Complete `.vibe/agents/reviewer.toml` so `enabled_tools` grants read/search
     only (no `write_file`/`edit_file`/`bash`).
   - *Acceptance:* verify check 3 passes (`enabled_tools` set, none banned).
4. **Trace and least-change fix a permission denial.** *(machine-checked: check 2)*
   - *Objective (Analyze):* trace a denial to the exact rule that caused it and
     fix it with the *smallest* correct change — the L300 debugging move.
   - *Why it matters:* over-broad "just allow everything" fixes are how blast
     radius creeps; least privilege is the discipline being graded.
   - `.vibe/config.toml` sets `[tools.bash] permission = "never"`, so the agent
     cannot run `pytest`. Change the ONE line to `permission = "ask"` (least
     privilege, not a blanket allow).
   - *Acceptance:* verify check 2 passes (bash permission is `ask`, not `never`).
5. **Wire a stdio MCP server (optional stretch).**
   - *Objective (Analyze):* choose the right MCP transport and confirm the config
     is well-formed before a run depends on it.
   - Add an MCP server to `.vibe/config.toml` using the `stdio` transport (a
     `command` + `args`), e.g. a local fetch server via `uvx`.
   - *Acceptance:* the TOML parses (e.g. `python3 -c "import tomllib,sys; tomllib.load(open('.vibe/config.toml','rb'))"`).
6. **Run a bounded headless job.**
   - *Objective (Analyze):* make a non-interactive run safe and CI-ready by
     bounding turns/cost and choosing a parseable output format.
   - *Why it matters:* unbounded automation is how a headless run loops or
     overspends; bounding is what makes it production-safe.
   - Prove non-interactive, cost-bounded automation:
     `vibe -p "List the files in app/ and stop" --max-turns 1 --max-price 0.05 --output json --auto-approve`
     (in `-p` mode a tool call needs approval; `--auto-approve` / `--yolo`
     allows it non-interactively — see `vibe --help`)
   - *Acceptance:* the output is a single parseable JSON object — suitable for CI.

All flags above are from `vibe --help` (2.24.0): `-p/--prompt`, `--agent`,
`--enabled-tools`, `--max-turns`, `--max-price`, `--output {text,json,streaming}`.

---

## When you are done

`bash verify/check.sh starter` reports **3 passed, 0 failed**, and you have
completed the three CLI exercises (plan-mode explore, MCP wiring, bounded
headless run). You have driven an advanced run across all the levers the course
grades: mode choice, delegated-tool scoping, denial tracing, and bounded
automation. **Next:** VIBE-400 (Expert) takes this into building extensions —
hooks and custom agent profiles — and optimizing a run against a stated
constraint.
