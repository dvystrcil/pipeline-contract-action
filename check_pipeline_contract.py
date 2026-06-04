#!/usr/bin/env python3
"""AST contract validator for OWUI Pipeline files.

Closes ACs 2-5 of dvystrcil/homelab#25. Catches the shape bugs that have
shipped to prod twice (2026-05-08, 2026-05-09) without the test ladder
catching them: sync inlet/outlet, missing `pipelines: list[str]` Valves
field, missing instance attributes set in __init__.

Pure AST — no module import side effects, no OWUI runtime dependency, no
network access. Safe to run in any CI environment.

Checks (one Pipeline class per file is assumed):

  AC2 — `inlet` and `outlet` methods (when present) are `async def`
  AC3 — `on_startup`, `on_shutdown`, `on_valves_updated` (when present)
        are `async def`
  AC4 — nested `Valves` class has a `pipelines` annotation
  AC5 — `__init__` assigns `self.type`, `self.name`, `self.valves`

Files that do NOT define a `class Pipeline` are skipped (helper modules,
test files, etc. are not under scrutiny).

Usage:
    python3 check_pipeline_contract.py pipelines/**/*.py
    python3 check_pipeline_contract.py path/to/single.py

Exit code: 0 if every Pipeline class passes every applicable check; 1 if
any violation found. Output: one line per violation in
`<file>:<line>:<col>: <message>` format, with parallel GHA-style
`::error file=...,line=...,col=...::<msg>` lines when GITHUB_ACTIONS=true.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

LIFECYCLE_METHODS = {"on_startup", "on_shutdown", "on_valves_updated"}
ASYNC_METHODS_WHEN_PRESENT = {"inlet", "outlet"} | LIFECYCLE_METHODS
REQUIRED_INSTANCE_ATTRS = {"type", "name", "valves"}
GHA = os.environ.get("GITHUB_ACTIONS") == "true"


def emit(path: str, line: int, col: int, msg: str) -> None:
    print(f"{path}:{line}:{col}: {msg}", file=sys.stderr)
    if GHA:
        print(f"::error file={path},line={line},col={col}::{msg}")


def find_pipeline_class(tree: ast.Module) -> ast.ClassDef | None:
    """Return the top-level `class Pipeline:` node, or None."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Pipeline":
            return node
    return None


def find_nested_class(parent: ast.ClassDef, name: str) -> ast.ClassDef | None:
    for node in parent.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def check_async_methods(cls: ast.ClassDef, path: str) -> int:
    """ACs 2 + 3 — every present `inlet`/`outlet`/lifecycle is `async def`."""
    violations = 0
    for name in ASYNC_METHODS_WHEN_PRESENT:
        m = find_method(cls, name)
        if m is None:
            continue
        if not isinstance(m, ast.AsyncFunctionDef):
            emit(path, m.lineno, m.col_offset,
                 f"method `{name}` must be `async def` (was `def`)")
            violations += 1
    return violations


def check_valves_pipelines_field(cls: ast.ClassDef, path: str) -> int:
    """AC4 — nested `class Valves` has an annotation `pipelines: ...`."""
    valves = find_nested_class(cls, "Valves")
    if valves is None:
        emit(path, cls.lineno, cls.col_offset,
             "Pipeline class is missing a nested `class Valves(...)`")
        return 1
    for node in valves.body:
        # AnnAssign — `pipelines: list[str] = []`
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == "pipelines":
            return 0
    emit(path, valves.lineno, valves.col_offset,
         "Valves class is missing required field `pipelines: list[str]`")
    return 1


def check_init_assigns_attrs(cls: ast.ClassDef, path: str) -> int:
    """AC5 — `__init__` assigns `self.type`, `self.name`, `self.valves`."""
    init = find_method(cls, "__init__")
    if init is None:
        emit(path, cls.lineno, cls.col_offset,
             "Pipeline class is missing `__init__` — cannot verify "
             "self.type / self.name / self.valves assignment")
        return 1

    assigned: set[str] = set()
    for node in ast.walk(init):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr in REQUIRED_INSTANCE_ATTRS
            ):
                assigned.add(target.attr)

    missing = REQUIRED_INSTANCE_ATTRS - assigned
    if missing:
        for attr in sorted(missing):
            emit(path, init.lineno, init.col_offset,
                 f"__init__ does not assign `self.{attr}` (required)")
        return len(missing)
    return 0


def check_file(path: str) -> int:
    """Run every check against one file. Returns violation count."""
    try:
        source = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        emit(path, 1, 0, f"could not read: {e}")
        return 1
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        emit(path, e.lineno or 1, e.offset or 0, f"syntax error: {e.msg}")
        return 1

    cls = find_pipeline_class(tree)
    if cls is None:
        # Not a Pipeline file — silently skip.
        return 0

    n = 0
    n += check_async_methods(cls, path)
    n += check_valves_pipelines_field(cls, path)
    n += check_init_assigns_attrs(cls, path)
    return n


def main(argv: list[str]) -> int:
    if not argv:
        print("no files to check")
        return 0

    total = 0
    pipeline_files = 0
    for arg in argv:
        if not Path(arg).is_file():
            emit(arg, 1, 0, "not a file")
            total += 1
            continue
        violations = check_file(arg)
        if violations:
            total += violations
        else:
            # Differentiate "no Pipeline class" from "Pipeline class is clean".
            try:
                src = Path(arg).read_text(encoding="utf-8")
                tree = ast.parse(src, filename=arg)
                if find_pipeline_class(tree) is not None:
                    pipeline_files += 1
            except (OSError, SyntaxError):
                pass

    if total == 0:
        print(f"OK — {pipeline_files} Pipeline file(s) checked, 0 violations")
        return 0
    print(f"FAIL — {total} violation(s) across the inputs", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
