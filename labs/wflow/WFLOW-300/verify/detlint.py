"""Determinism linter for Workflows entrypoints (WFLOW-300 verify tool).

Mirrors the Workflows determinism sandbox's banned-call list (building-workflows/workflows/
determinism.md): workflow code must not call non-deterministic standard-library APIs or do I/O
directly. It lints only the `run` entrypoint(s) of classes decorated with `@workflow.define`;
activities are allowed to be non-deterministic and are not linted.

Usage: python detlint.py <path-to-module.py>   (exit 0 = clean, non-zero = violations)
"""
from __future__ import annotations

import ast
import sys

BANNED_CALL_SUFFIXES = (
    "datetime.now", "datetime.utcnow", "datetime.today",
    "time.time", "time.monotonic",
    "uuid.uuid1", "uuid.uuid3", "uuid.uuid4", "uuid.uuid5",
    "random.random", "random.randint", "random.choice", "random.uniform",
    "os.getcwd", "os.listdir",
    "requests.get", "requests.post", "httpx.get", "httpx.post",
)
BANNED_NAMES = ("open",)
BANNED_ATTR_ACCESS = ("os.environ",)


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_entrypoint_class(cls: ast.ClassDef) -> bool:
    for dec in cls.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        name = _dotted(target) or ""
        if name.endswith("workflow.define") or name.endswith("define"):
            return True
    return False


def _lint_function(fn: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name and (name.endswith(BANNED_CALL_SUFFIXES) or name in BANNED_NAMES):
                violations.append(f"line {node.lineno}: banned call {name}()")
        elif isinstance(node, ast.Attribute):
            name = _dotted(node)
            if name in BANNED_ATTR_ACCESS:
                violations.append(f"line {node.lineno}: banned access {name}")
    return violations


def lint_entrypoints(path: str) -> list[str]:
    tree = ast.parse(open(path).read(), filename=path)
    out: list[str] = []
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and _is_entrypoint_class(cls):
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "run":
                    out.extend(f"{cls.name}.run {v}" for v in _lint_function(item))
    return out


if __name__ == "__main__":
    problems = lint_entrypoints(sys.argv[1])
    for p in problems:
        print("  DET:", p)
    sys.exit(1 if problems else 0)
