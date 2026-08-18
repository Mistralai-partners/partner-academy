# VIBE-400 Lab - Extend and Operate Vibe Code (hands-on)

**Tier:** L400 (Expert - Evaluate / Create). **Behavior this lab grades:**
*build, extend, and operate* Vibe Code as production infrastructure - author
hooks that gate and audit the agent loop, design least-privilege agent
profiles and a team permission posture, and assemble a headless CI gate that
turns a model verdict into an exit code.

**Prereqs:** `vibe` CLI installed (`vibe --version` ≥ 2.24), Python 3.11+
(for `tomllib`). `MISTRAL_API_KEY` is needed **only** for the optional live
runs - every graded check runs offline.

**How to work it:** work in `starter/`. Run `bash ../verify/check.sh starter`
(or from the lab root: `bash verify/check.sh starter`) any time. You are
**done when it reports 8 passed, 0 failed.** All eight checks are
machine-graded and deterministic. Reference solution: `solution/`.

**Ramp note:** Task 1 (the hook chain: four checks, one `hooks.toml` plus three
scripts) is the build-heavy centerpiece — budget the bulk of your time there.
Tasks 2–4 are fast, high-leverage *design* decisions (scope a profile, a
subagent, a permission posture) you can land quickly to build momentum; Task 5
(the CI gate) is a focused parser. A reasonable order is 2 → 3 → 4 → 1 → 5, but
the checks are independent, so work them in whatever order suits you.

Grounding: every field, flag, and wire-protocol shape below comes from the
installed CLI (`vibe --help`, `vibe.core.hooks`) and the pinned Vibe docs
(`configuration`, `agents`, `safety-approvals-permissions`, `work-with-cli`).
No invented flags.

---

## Task 1 - Extend the agent loop with hooks *(checks 1–4)*

- **Objective (Create):** extend the runtime with a `hooks.toml` that *guards*,
  *audits*, and *gates* the loop, and write the three hook scripts that
  implement the wire protocol.
- **Scenario:** you operate Vibe Code in CI. You need a fail-closed guard that
  blocks destructive shell commands, an audit trail of every tool that ran,
  and a record of turn boundaries - none of which the base agent gives you.
- **Do:**
  1. In `.vibe/hooks.toml`, make the `pre_tool` guard **fail-closed**
     (`strict = true`) and **scoped** (`match = "bash"`); add a `post_tool`
     audit hook and a `post_agent` gate hook. Remember: `match` and `strict`
     are **tool-hook only** - the loader rejects them on `post_agent`.
  2. Complete `.vibe/hooks/guard.py`: read the `pre_tool` invocation on stdin;
     if `tool_input.command` matches a destructive pattern, print
     `{"decision":"deny","reason":"..."}` (exit 0). Leave stdout empty to allow.
  3. Complete `.vibe/hooks/audit.py`: on a `post_tool` invocation, append a
     line (tool name, status, duration) to `audit.log`.
  4. Complete `.vibe/hooks/gate.py`: on a `post_agent` invocation, append a
     turn-boundary line to `audit.log`.
- **Wire protocol (grounded):** stdin is the invocation JSON (`pre_tool`:
  `tool_name`, `tool_call_id`, `tool_input`; `post_tool` adds `tool_status`,
  `tool_output_text`, `duration_ms`, …). Response is **exit 0 + a JSON object**
  on stdout: `decision` (`allow`|`deny`), `reason`, `system_message`,
  `hook_specific_output` (`tool_input` rewrite for `pre_tool`,
  `additional_context` append for `post_tool`). **Empty stdout = passthrough.**
  Non-zero exit / bad JSON = failure; under `strict` that failure **escalates**
  (a `pre_tool` denies the call).
- **Hint (evidence, not fix):** run your guard by hand -
  `printf '{"tool_input":{"command":"rm -rf /"},"tool_name":"bash"}' | python3 .vibe/hooks/guard.py`.
  If nothing prints, the guard is allowing it.
- **Acceptance:** checks 1–4 - `hooks.toml` declares a strict+scoped `pre_tool`
  guard, a `post_tool` audit, and a `post_agent` gate; the guard denies
  `rm -rf` and passes safe commands; the audit hook writes a marker; the gate
  hook writes a turn boundary.
- **See it fire for real (optional):** from `solution/`,
  `VIBE_LIVE=1 MISTRAL_API_KEY=... bash ../verify/check.sh solution` runs a
  bounded `vibe -p` and shows the hooks firing in a live run.

## Task 2 - Design a least-privilege agent profile *(check 5)*

- **Objective (Evaluate/Create):** design the best-justified profile for
  reviewing an **untrusted fork PR** and defend the tool scope.
- **Scenario:** an agent that reviews code from strangers should not be able to
  edit the tree or run the shell. The blast radius must equal the job.
- **Do:** in `.vibe/agents/ci-reviewer.toml`, keep `agent_type = "agent"`
  (user-facing, selectable via `vibe --agent ci-reviewer`) and cut
  `enabled_tools` to read/search only (e.g. `read_file`, `grep`). Note that
  `safety = "safe"` is a **visual hint only** - it does not enforce; the tool
  scope does.
- **Hint:** ask "what is the *minimum* a reviewer needs to read a diff and
  comment?" Anything that writes or executes is over-scope here.
- **Acceptance:** check 5 - profile is `agent_type = "agent"` with
  `enabled_tools` present and none of `write_file`/`search_replace`/`bash`/….

## Task 3 - Design a delegation subagent *(check 6)*

- **Objective (Create):** build a research helper the model can **delegate to**
  via the `task` tool, isolated to read-only.
- **Scenario:** the parent agent wants to fan out background exploration
  without handing a helper write or shell access.
- **Do:** in `.vibe/agents/researcher.toml`, set `agent_type = "subagent"`
  (delegation-only - NOT user-selectable; spawned through the `task` tool;
  returns text-only) and scope `enabled_tools` to read/search only.
- **Hint:** the difference that matters here is one field -
  `agent_type` - plus dropping the write tool.
- **Acceptance:** check 6 - `agent_type = "subagent"`, read/search only.

## Task 4 - Design the team permission posture *(check 7)*

- **Objective (Evaluate):** choose the best-justified per-tool posture for a
  shared repo and justify why a blanket allow is wrong.
- **Scenario:** "just allow everything" is how blast radius creeps. A denylist
  match must win **even under an `always` / `auto-approve` posture** - that is
  why a sensitive pattern still blocks.
- **Do:** in `.vibe/config.toml`, stop blanket-allowing the shell: set
  `[tools.bash] permission = "ask"` and add
  `deny = ["rm -rf *", "git push", "git reset --hard"]` (optionally extend
  `allow` with known-safe project commands). Reason about precedence: CLI flags
  > env vars > **project `.vibe/config.toml`** > user `~/.vibe/config.toml`,
  and a selected `--agent` profile overrides the merged config for that run.
- **Hint:** the failing check names the exact rule - `[tools.bash].permission`.
- **Acceptance:** check 7 - bash is not `always`; a destructive-command
  denylist is present.

## Task 5 - Build a headless CI review gate *(check 8)*

- **Objective (Create/Analyze):** assemble a reproducible, non-interactive gate
  that converts a `vibe -p --output json` transcript into a CI exit code.
- **Scenario:** a gate that cannot fail is not a gate. It must block a
  `REQUEST_CHANGES` verdict and a broken run, not just wave through `APPROVE`.
- **Do:** complete `ci/parse_verdict.py` so it reads the JSON transcript on
  stdin, finds the **last assistant message**, and maps its verdict line:
  `VERDICT: APPROVE` → exit 0, `VERDICT: REQUEST_CHANGES` → exit 1, anything
  else (no assistant message, no verdict, invalid JSON) → exit 3.
  `ci/review-gate.sh` already wires stdin/file input and the live mode.
- **The reproducible pipeline command (live):**
  `MISTRAL_API_KEY=... ci/review-gate.sh --live "Review app_sample.py. End with a line 'VERDICT: APPROVE' or 'VERDICT: REQUEST_CHANGES'."`
  It runs `vibe -p --agent ci-reviewer --output json --max-turns 4 --trust
  --auto-approve` and pipes the transcript into your parser.
- **Hint:** test offline against the fixtures -
  `ci/review-gate.sh ci/samples/rejected.json; echo $?` must print `1`.
- **Acceptance:** check 8 - gate exits 0 / 1 / 3 for approved / rejected /
  malformed transcripts.

---

## When you are done

`bash verify/check.sh starter` reports **8 passed, 0 failed**. You have
*extended* Vibe Code (a fail-closed hook chain that fires for real), *designed*
two least-privilege agent profiles and a team permission posture, and *built* a
headless CI gate that can actually block a bad change. Every artifact runs and
meets an acceptance contract - the L400 bar. **Next:** apply these to your own
repo - commit `.vibe/` so the team can review the safety decisions, and wire
`ci/review-gate.sh --live` into your pipeline.

---

### Flag/field provenance
- CLI flags (`-p`, `--output {text,json,streaming}`, `--max-turns`,
  `--agent`, `--enabled-tools`/`--disabled-tools`, `--trust`, `--auto-approve`):
  `vibe --help` (2.24.0).
- Hook schema + wire protocol (`type`, `command`, `match`, `strict`, `timeout`;
  stdin invocation fields; `decision`/`reason`/`hook_specific_output`;
  empty-stdout passthrough; strict escalation; `post_tool` fires only when the
  body ran): installed `vibe.core.hooks` (models/handlers/manager) and
  `cli/configuration.md` (Hooks) at the pinned SHA. `hooks.toml` lives at
  `<project>/.vibe/hooks.toml` (trusted) or `$VIBE_HOME/hooks.toml`.
- Agent profiles (`agent_type` `agent`/`subagent`, `enabled_tools`, per-tool
  `permission`, `safety` is visual-only, `task`-spawned subagents): `cli/agents.md`.
- Permissions/precedence (`[tools.<name>] permission`, bash `allow`/`deny`,
  denylist-wins, trust): `safety-approvals-permissions.md`, `cli/configuration.md`.
