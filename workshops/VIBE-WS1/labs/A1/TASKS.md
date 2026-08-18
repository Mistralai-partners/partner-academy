# A1 - Read before you write: plan a change you never make · TASKS

- **Objective:** explore an unfamiliar Python repo in the read-only
`plan` agent, use @-file references to focus the agent on the refund path, and
produce a correct change-plan that names the exact files, functions, and the test
to add, all without editing a single file.

- **Scenario (why this matters on the job):** you get added to services you have
never seen and asked to change them under time pressure. The practitioner move is
to read first and hand leadership a reviewable plan before you touch code. A
read-only planning pass gives you that plan with zero risk of an accidental edit.

**Prerequisites:**
- `vibe` CLI installed and working (`vibe --version` prints a version).
- Python 3.10 or newer and `pytest` available (`python -m pytest --version`).
- Starter project in `starter/`, this file, `VERIFY.md`, the reference plan in
  `solution/change-plan.md`, and the checker `solution/verify/plan_check.py`.

- **Done when:** all 3 checks pass.
- `git status` in your working copy is clean (no files changed).
- `python /ABS/PATH/TO/solution/verify/plan_check.py my-change-plan.md` prints PASS.
- Your saved `my-change-plan.md` names the same target files and functions as
   `solution/change-plan.md` (that is what check 2 confirms).

---

## Setup (about 5 minutes)

- Copy the starter into a fresh working directory so your edits and git history
   stay separate from the lab materials:

   ```bash
   cp -R starter ~/payments-service-a1
   cd ~/payments-service-a1
   ```

- Make it a git repo and commit a baseline. This is what lets `git status` and
   `git diff` prove later that you changed nothing:

   ```bash
   git init
   git add -A
   git commit -m "baseline"
   ```

- Confirm the existing tests pass before you start (this lab has no failing
   test; the work is read-only planning):

   ```bash
   python -m pytest
   ```

- You should see all tests pass.

- Confirm the read-only planning agent launches from inside the repo:

   ```bash
   vibe --agent plan
   ```

- The first launch in a folder that is not yet trusted prints a trust warning
   and ignores project config until you trust it. You can accept the trust
   prompt, or relaunch with `vibe --agent plan --trust`. The `plan` agent is
   read-only: it auto-approves safe read tools and does not write files or run
   mutating tools.

---

## Steps (live in the `vibe` CLI)

### Step 1 - Launch the read-only planning agent

- **Objective:** start a session that cannot edit the repo.

- **Do:** from inside `~/payments-service-a1`, run `vibe --agent plan`.

- **Hint:** if you are unsure the session is read-only, ask the agent to list the
tools it is allowed to use. A planning session exposes read tools such as
`read_file` and `grep`, not `write_file` or `edit`. Do not fix anything yet.

- **Acceptance:** the session is open and reports read-only tools.

### Step 2 - Orient in the repo

- **Objective:** map how a refund flows through the code before you
propose anything.

- **Do:** ask the agent for a short tour of the service. Read `README.md` and
`TICKET.md` first so you know what is being asked.

- **Hint:** the evidence you need is the call path, not a fix. Trace how a request
reaches the refund logic and where a refund is recorded. Look for the handler,
the domain function it calls, and the store it writes to.

- **Acceptance:** you can name, in one sentence each, where a refund request enters
and where a refund is persisted.

### Step 3 - Focus the agent with @-references

- **Objective:** pin the exact files that the change would touch so the
agent reasons about the right surface.

- **Do:** in the chat input, type `@` and pin the refund path files, for example:

```
@src/payments_service/api.py @src/payments_service/refunds.py @src/payments_service/store.py @tests/test_refunds.py
```

- Typing `@` autocompletes project files; you can also paste an absolute path.

- **Hint:** if the agent talks about files outside the refund path, you have not
pinned enough context. Re-pin the three source files plus the test file and ask
it to reason only about those. The point is to focus, not to widen.

- **Acceptance:** the agent's reasoning references `handle_refund`,
`process_refund`, and the `PaymentStore` methods.

### Step 4 - Iterate to a concrete change-plan

- **Objective:** produce a plan that names exact files, functions, the
store lookup to add, assumptions, and the test to add. No code edits.

- **Do:** ask the agent for a change-plan for the PAY-482 ticket. Push it until the
plan names:
- the endpoint handler to change (`handle_refund` in `api.py`),
- the domain function to change (`process_refund` in `refunds.py`),
- the store change (a lookup by idempotency key in `store.py`),
- the acceptance test to add in `tests/test_refunds.py`,
- and your assumptions.

- **Hint:** if the plan is vague ("update the refund code"), the evidence that it
is not yet reviewable is that a teammate could not act on it. Ask "which function
in which file, and what new test," and keep the answer to targets, not code. Do
not ask it to implement anything.

- **Acceptance:** the plan text names the file set and function names above.

### Step 5 - Save the plan to a file (still no edits)

- **Objective:** capture the plan as `my-change-plan.md` in your working
directory so leadership and the checker can read it.

- **Do:** copy the agent's change-plan into a new file `my-change-plan.md` at the
repo root. `vibe` also saves plans under `~/.vibe/plans/`; you can copy from
there. Do not let the agent write into the source tree.

- **Hint:** the file you create for your own notes is fine because it is not part
of the committed baseline. If `git status` later shows a source file changed, you
edited the wrong thing. `my-change-plan.md` is expected to appear as untracked,
which is not a change to the baseline.

- **Acceptance:** `my-change-plan.md` exists and contains the plan.

### Step 6 - Self-check

- **Objective:** confirm your plan names the required targets and that
the repo is untouched.

**Do:**

```bash
git status
python /ABS/PATH/TO/solution/verify/plan_check.py my-change-plan.md
```

- **Hint:** if `plan_check.py` prints FAIL with missing symbols, go back to Step 4
and ask the agent to name the specific file or function it listed as missing. Do
not edit the plan by guessing; get the target from the read-only agent. If
`git status` shows a tracked source file changed, see the unblock in `VERIFY.md`.

- **Acceptance:** `git status` is clean of source changes and `plan_check.py`
prints PASS. See `VERIFY.md` for the full acceptance and the reasoning behind it.

---

## Stretch - Prove the read-only guarantee two ways

- Relaunch with the tool set explicitly restricted to read tools and confirm you
get the same plan:

```bash
vibe --agent plan --enabled-tools read_file --enabled-tools grep
```

- The `--enabled-tools` flag is repeatable and supports globs and `re:` regex.
Re-produce the change-plan and confirm it names the same files and functions as
before. The plan should be identical in its targets. This shows the plan came
from reading the code, not from any ability to change it.

---

## What you learned

- The read-only `plan` agent lets you analyze an unfamiliar repo with zero risk
  of an accidental edit.
- @-references focus the agent on the exact surface a change would touch, which
  produces a plan a teammate can act on.
- A reviewable plan names files, functions, the store change, assumptions, and
  the test to add, before any code is written.

- **Next:** go deeper on planning and safe execution across surfaces in
**VIBECODE-300**.
