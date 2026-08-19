# vibe-demo-app

A tiny in-memory inventory tracker. It exists only as a safe, self-contained
practice project for the Mistral Vibe Code course: no network calls, no secrets, no
files written, nothing destructive. Point Vibe Code at this folder and try the labs.

This project is managed with [uv](https://docs.astral.sh/uv/). uv creates the
environment and installs dependencies for you on first run.

Run it:

```bash
uv run python -m app.cli
```

Run the tests:

```bash
uv run pytest -q
```
