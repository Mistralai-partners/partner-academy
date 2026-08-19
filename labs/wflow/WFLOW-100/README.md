<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Fundamentals (WFLOW-100)

# WFLOW-100 Lab: your first durable workflow

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

The hands-on companion to WFLOW-100. You scaffold a Workflows project, define a
minimal `hello-world` workflow, run a worker, and trigger your first execution.
These steps run in your own shell and need `uv`, network access, and a Mistral
account (`MISTRAL_API_KEY`); the workflow runs on a Workflows worker connected to
the platform, not standalone.

## Steps

1. **Scaffold a project** (this provides the worker and a `Makefile`):
   ```bash
   uvx mistralai-workflows-cli@latest setup
   ```
2. **Confirm the SDK is installed:**
   ```bash
   uv run python verify.py   # prints: Workflows is installed successfully!
   ```
3. **Use the workflow in this lab:** copy `src/workflows/hello.py` into your
   scaffolded project's `src/workflows/`, replacing the generated example.
4. **Run it:** start the worker (the scaffold registers workflows and polls via
   `workflows.run_worker`) with `make start-worker` in one terminal, then trigger an
   execution in another:
   - CLI: `make execute workflow=hello-world input='{"name": "World"}'`
   - SDK: `uv run python run_client.py` (uses `client.workflows.execute_workflow`)

## Done when

The worker logs `Result: {'result': 'Hello, World! Welcome to Mistral Workflows.'}`
and the returned execution shows a `workflow_name`, an `execution_id`, and a
`status`.
