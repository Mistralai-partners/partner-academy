# A4 Tasks: Run Vibe Code you can trust unattended

## Behavior this lab builds

- You will make `vibe` run headless as a CI-style read-only reviewer that is structurally
incapable of editing the branch or overspending. You will prove it with an empty
`git diff` and the absence (or denial) of write tool calls, not with a hopeful prompt.

## Prerequisites

- `vibe` CLI installed (verified against vibe 2.24.0).
- `MISTRAL_API_KEY` exported for any live `vibe -p` run.
- `git` and `python3` on PATH.

## Done when

- A headless reviewer run exits 0.
- `git diff` is empty after the run.
- Branch (a): the `--output json` array has no `write_file`/`edit` tool calls. OR
- Branch (b): the pre-tool hook fired and denied the edit while the run still exited 0.

---

## Setup (target: 5 minutes)

- Copy the starter into a working directory and enter it.

   ```sh
   cp -r starter /tmp/release-tools
   cd /tmp/release-tools
   ```

- Make it a git repo and commit a baseline. This matters: an empty `git diff` is only
   a meaningful safety proof if there is a committed baseline to diff against.

   ```sh
   git init
   git add -A
   git commit -m baseline
   ```

- Install ONE guard.

   - Branch (a), agent profile:

     ```sh
     mkdir -p ~/.vibe/agents
     cp ../path/to/solution/reviewer.toml ~/.vibe/agents/reviewer.toml
     ```

   - Branch (b), pre-tool hook. Copy the hook into the project and set the ABSOLUTE
     path to `block_writes.py` inside it (relative paths are unreliable in hooks):

     ```sh
     mkdir -p .vibe
     cp ../path/to/solution/hooks.toml .vibe/hooks.toml
     # then edit .vibe/hooks.toml: replace /ABS/PATH/TO with the real absolute path
     ```

- Confirm headless mode works at all with a trivial run.

   ```sh
   vibe -p "hello" --output json --max-turns 1 --auto-approve --trust
   ```

- You should get a JSON array back and exit code 0. (This is a live, paid call; it is
   tiny by design.)

---

## Task 1: Prove the prompt alone is not a boundary

- **Objective:** Judge whether a "read-only" instruction in the prompt
  actually prevents edits.
- **Scenario:** Before adding any guard, run a headless prompt that asks the model to be
  read-only but leaves all tools enabled, and tell it to bump the version.

  ```sh
  vibe -p "You are a read-only reviewer. Do not edit anything. Now bump __version__ in src/release_tools/version.py to 1.5.0." \
    --output json --max-turns 6 --max-price 0.05 --auto-approve --trust > naive.json
  git diff
  ```

- **Hint:** Look at `git diff` and search `naive.json` for `edit` or `write_file`. Ask
  yourself what stopped the edit. Nothing did if the file changed. Do not fix it yet.
- **Acceptance:** You can state whether the file was edited and explain that the prompt
  is a request, not an enforced boundary. Reset before moving on: `git checkout -- .`

---

## Task 2: Build the guard (pick ONE branch)

### Branch (a): custom read-only agent profile

- **Objective:** Construct a guarded headless run using `--agent reviewer`.
- **Scenario:** Author the guarded command in `ci/review.sh` (or run it directly). The
  reviewer profile allow-lists `read_file` + `grep`, so write and edit tools do not
  exist for the agent.

  ```sh
  vibe -p "Review the diff in diff-to-review.patch and summarize the risks" \
    --agent reviewer --output json --max-turns 6 --max-price 0.05 \
    --auto-approve --trust > review-agent.json
  echo "exit: $?"
  git diff
  ```

- **Hint:** If the run errors that a tool is unavailable, that is the posture working,
  not a bug. Compare your command to the flags documented in `starter/ci/review.sh`. The
  evidence you want is an empty `git diff` and no `write_file`/`edit` entries in the JSON.
- **Acceptance:** Exit 0, `git diff` empty, `review-agent.json` is a valid JSON array
  with no write/edit tool calls. See `VERIFY.md` branch (a).

### Branch (b): pre-tool hook that denies writes

- **Objective:** Construct a guarded run where a pre-tool hook denies
  write/edit even under an adversarial prompt.
- **Scenario:** With `.vibe/hooks.toml` installed (absolute path set), deliberately ask
  the model to edit the version file.

  ```sh
  vibe -p "Bump __version__ in src/release_tools/version.py to 1.5.0 by editing the file" \
    --output json --max-turns 6 --max-price 0.05 --auto-approve --trust > review-hook.json
  echo "exit: $?"
  git diff
  ```

- **Hint:** Search `review-hook.json` for the deny reason string from `block_writes.py`.
  If the file changed anyway, check that the hook `command` uses an absolute path and
  that the folder is trusted. The evidence is the deny reason plus an empty `git diff`.
- **Acceptance:** Exit 0, the hook deny reason appears in the JSON stream, `git diff`
  empty. See `VERIFY.md` branch (b).

---

## Stretch: Prove the turn cap, do not assume it

- **Objective:** Confirm the budget guardrail actually stops the run.
- **Scenario:** Re-run your guarded reviewer with a deliberately large task and a tight
  turn cap.

  ```sh
  vibe -p "Read every file in this repo, then write a 20-section audit of each function" \
    --agent reviewer --output json --max-turns 3 --max-price 0.05 \
    --auto-approve --trust > capped.json
  ```

- **Hint:** Search `capped.json` for `<vibe_stop_event>` and the phrase about a turn
  limit being reached. The guardrail is proven when the run stops itself, not when you
  hope it would.
- **Acceptance:** `capped.json` contains a `<vibe_stop_event>` interruption marker
  (for example, "Turn limit of 3 reached"), and `git diff` is still empty.

---

## What you learned

- A prompt is not a permission boundary. "You are read-only" is a request the model can
  ignore. Least privilege must live in the agent profile (allow-list tools) or in a
  pre-tool hook (deny write/edit). Posture, not politeness.
- The real proof of an unattended run is objective: exit code, an empty `git diff`, and
  the absence or denial of write tool calls, plus a cost/turn ceiling that demonstrably
  stops the run.

## Next

- Continue to **VIBECODE-400** for the full treatment of Vibe Code configuration layers,
permission scopes, hooks, and multi-surface unattended operation.
