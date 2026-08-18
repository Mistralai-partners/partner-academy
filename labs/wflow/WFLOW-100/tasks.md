# WFLOW-100 Lab Tasks: Your First Durable Workflow

**Tier:** L100 Fundamentals. **Behavior:** scaffold, define, run, and verify a minimal durable workflow.

## Task 1: Install and scaffold
Scaffold a project with `uvx mistralai-workflows-cli@latest setup`, then confirm the SDK with `uv run python verify.py`.

## Task 2: Define and run the workflow
Copy `src/workflows/hello.py` into the scaffold, start the worker, and trigger the `hello-world` workflow from the CLI and the SDK (`run_client.py`).

**Done when:** the execution completes and returns `Hello, World! Welcome to Mistral Workflows.`
