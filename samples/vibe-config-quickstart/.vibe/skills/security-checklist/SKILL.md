---
name: security-checklist
description: Reviews code against a security and correctness checklist (input validation, error handling, no secrets, docstrings and type hints). Use when reviewing code, or when the user mentions a code review, security, or a correctness check.
---

# Security and correctness checklist

Apply every item below to the code under review. For each item, state pass or
fail with the file and function; if it fails, give the one-line fix.

Read the full checklist in `references/checklist.md` and work through it item by
item. The headline checks are:

1. Input validation at the boundary: reject impossible values (negative amounts,
   a refund larger than the order total) instead of returning a wrong result.
2. Error handling: no bare `except`; failures surface a clear error.
3. No secrets in source (keys, tokens, passwords).
4. Conventions: public functions have docstrings and type hints (see src/AGENTS.md).

Report findings grouped by severity (High, Medium, Low).
