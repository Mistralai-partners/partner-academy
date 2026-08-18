<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Fundamentals (WFLOW-100)

# WFLOW-100 Lab: your first durable workflow

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
4. **Run it:** start the worker with the scaffold's `make start-worker` in one
   terminal, then trigger an execution in another:
   - CLI: `make execute workflow=hello-world input='{"name": "World"}'`
   - SDK: `uv run python run_client.py`

## Done when

The worker logs `Result: {'result': 'Hello, World! Welcome to Mistral Workflows.'}`
and the returned execution shows a `workflow_name`, an `execution_id`, and a
`status`.
