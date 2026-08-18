# VIBE-TSE1 Lab - Run the demo, scope the deal (tech sales)

**Tier:** TSE (Tech Sales Essentials - Apply-dominant). **Behavior this lab
grades:** stand up and run the Vibe Code happy-path demo for a customer on a real
repo, then qualify the opportunity - test candidate use cases against the four
marks of an iconic use case, place the deal in Discover/Deliver/Scale, pick the
surface and engagement type, and answer the on-premises objection while knowing
when to bridge to a solutions engineer.

**Prereqs:** `vibe` CLI installed (`vibe --version` >= 2.24) and
`MISTRAL_API_KEY` set (`vibe --setup`) for the demo tasks; Python 3.11+ for the
tests and the checker. The scoping tasks (4 and 5) need no key.

**The two halves of this lab.**

1. **The live demo (Tasks 1-3)** - the runnable happy path you perform on the
   projector: explore a customer repo read-only, have Vibe Code add a requested
   feature *with tests*, then produce a CI-ready result from a bounded headless
   run. The mini customer repo is `taskvault` (`app/vault.py`), and the feature
   request is in `FEATURE.md`.
2. **The scoping exercise (Tasks 4-5)** - the qualification call you run from
   `scenario.md`, recorded as a decision in `scoping.json`.

**How to work it:** work in `starter/`. Run `bash ../verify/check.sh starter`
any time. You are **done when it reports 5 passed, 0 failed**. Reference
solution: `solution/`.

**Trust note:** this repo ships a `.vibe/` folder, so Vibe loads its project
config only from a trusted directory. Accept the trust prompt in interactive
mode, or pass `--trust` for the non-interactive `-p` runs below (grants trust for
that one invocation; see `vibe --help`).

---

## 1. Open the customer repo read-only (the credibility on-ramp)

- **Objective (Apply):** open a repo you did not write with zero change risk by
  choosing the read-only `plan` agent - so the first thing the customer sees is
  the agent *understanding* their code, not touching it.
- **Scenario:** you are at the customer's screen. Before you change anything, you
  let the agent read the code and explain it. This is the moment that sells "one
  agent, three surfaces, running an understand-plan-act loop," not autocomplete.
- Run from `starter/`:
  ```bash
  vibe --agent plan --trust -p "Summarize what app/vault.py does and what feature FEATURE.md asks for" --output text
  ```
  Or start interactively with `vibe --agent plan`, then attach files with `@`:
  `Read @app/vault.py and @FEATURE.md and explain the requested change.`
- **Hint:** narrate what the agent is *allowed* to do, not just what it says. In
  `plan` it never proposes a write - that is the point you are making to the room.
- **Acceptance:** the run makes no edits (`git status` stays clean, or the files
  are byte-for-byte unchanged). This task is confirmed by eye; it is not a gate.

## 2. Have Vibe Code add the feature - with its tests *(gates 1 and 2)*

- **Objective (Apply):** delegate a real change and verify it, by switching to an
  edit-approving agent, naming the outcome, and keeping the tests as the
  acceptance gate.
- **Scenario:** the customer asked for `search(keyword)` (see `FEATURE.md`). You
  drive Vibe Code to plan it, implement it in `app/vault.py`, and write
  `tests/test_search.py` - live. A change that ships without tests is not a demo
  you want a customer to remember.
- Switch to the edit-approving agent and hand over the request. Interactive:
  `vibe --agent accept-edits`, then
  `Implement the search(keyword) method in @app/vault.py per @FEATURE.md and add tests in tests/test_search.py.`
  Non-interactive equivalent:
  ```bash
  vibe --agent accept-edits --trust -p "Implement Vault.search(keyword) in app/vault.py per FEATURE.md (case-insensitive substring match, empty keyword returns none, match the style of add) and add tests in tests/test_search.py" --max-turns 8 --output text
  ```
- **Hint:** `FEATURE.md` is the spec and `app/vault.py`'s `add` is the pattern to
  match. Read the diff before you accept it; a good demo shows you reviewing, not
  rubber-stamping.
- **Acceptance:** `python3 -m pytest -q` is green, and `tests/test_search.py`
  exists and calls `.search(` (gates 1 and 2).

## 3. Produce a CI-ready result from a bounded headless run *(gate 3)*

- **Objective (Apply):** show programmatic mode honestly - a non-interactive run,
  bounded, emitting machine-readable output - and position what its cost control
  does and does not guarantee.
- **Scenario:** the customer's team wants Vibe Code in CI. You show the same
  agent running headless, bounded on turns and price, writing a PR-style summary
  as JSON a pipeline could consume. This is where you make the honest claim about
  cost, not an overclaim.
- Run from `starter/`:
  ```bash
  vibe -p "Write a one-paragraph pull-request description for the change that added search() to app/vault.py with tests. Do not modify any files." \
    --max-turns 1 --max-price 0.10 --output json --auto-approve --trust > pr.json
  ```
  In `-p` mode a tool call needs approval; `--auto-approve` (alias `--yolo`)
  allows it non-interactively (see `vibe --help`).
- **Hint on the honesty point (this is graded knowledge, not just a demo):**
  `--max-turns` is the reliable bound on run length. Treat `--max-price` as a
  guardrail that *interrupts* a run, not a pre-authorized hard budget - the
  pinned docs say to treat reported cost as **indicative only** and not to rely
  on it for hard budget enforcement. Bound headless runs with turns and a
  restricted toolset (`--enabled-tools`), and say so plainly to IT.
- **Acceptance:** `pr.json` exists and parses as JSON (gate 3).

## 4. Qualify the opportunity against the four marks *(gate 4)*

- **Objective (Apply):** qualify a technical use case by testing each candidate
  in `scenario.md` against the four marks of an iconic use case, then choosing
  the surface, engagement type, and next step.
- **Scenario:** the discovery call surfaced two candidates. Only one is an iconic
  use case. Recording the call correctly is how you avoid proposing a workshop
  for a use case that is not ready.
- Read `scenario.md`, then edit `scoping.json`:
  - For **each** candidate, set the four `marks` (`strategically_valuable`,
    `highly_urgent`, `production_bound`, `feasible_within_six_months`) to `true`
    or `false`, and set `verdict` to `"ready"` or `"needs_scoping"`. A candidate
    is **ready only if all four marks are true**.
  - Set `primary_surface` to the surface the pilot's automation goal anchors on,
    `engagement_type` to the one that fits a single team automating a core
    workflow, and `recommended_next_step` to the Discover-phase move for a
    qualified use case.
- **Hint:** the four marks and the vocabulary for surface, engagement type, and
  next step are listed at the bottom of `scenario.md`. Read the two candidates
  against them; the difference between "ready" and "needs scoping" is whether a
  named owner and a production commitment exist.
- **Acceptance:** verify gate 4 passes (marks, verdicts, surface, engagement
  type, and next step all correct).

## 5. Handle the on-premises objection and know when to bridge *(gate 5)*

- **Objective (Apply):** answer the most common enterprise objection with the
  right pillar, offer the right proof, and recognize when a question is an SE
  bridge rather than something to bluff.
- **Scenario:** the security lead says the code cannot leave their environment,
  and an architect asks a deployment-config question you are not sure about.
  Handling both honestly is what earns the technical room's trust.
- In `scoping.json`, complete the `objection` section: set `primary_pillar` to
  the pillar that answers on-premises precisely, `offer_security_review` to
  whether you should offer a security review, and `bridge_to_solutions_engineer`
  to whether the architect's deep-config question should go to an SE.
- **Hint:** on-premises is answered by the pillar about running in the customer's
  own environment with their data, weights, and keys staying with them. A deep
  configuration question you are unsure of is a bridge, not a guess.
- **Acceptance:** verify gate 5 passes (pillar, security-review offer, and SE
  bridge all correct).

---

All Vibe commands and flags in this lab are from `vibe --help` (2.24.0):
`-p/--prompt`, `--agent` (`plan`, `accept-edits`, or a custom name), `--trust`,
`--max-turns`, `--max-price`, `--auto-approve`/`--yolo`, `--enabled-tools`,
`--output {text,json,streaming}`. File references with `@` are an interactive
feature from the CLI docs. No invented flags, paths, or tool names.

## When you are done

`bash verify/check.sh starter` reports **5 passed, 0 failed**, and you have run
the read-only explore in Task 1. You can now run the Vibe Code happy-path demo on
a customer's repo end to end - explore, feature-with-tests, CI-ready headless
result - and turn a discovery call into a qualified opportunity: the right
candidate against the four marks, the right surface and engagement type, the
next step, and an honest answer to the on-premises objection with a clean bridge
to a solutions engineer. **Next:** run a discovery role-play with your partner
manager, and take the hands-on ladder (VIBE-100 through VIBE-400) to deepen your
own credibility with the CLI, configuration, agents, skills, and MCP.
