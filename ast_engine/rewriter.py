"""Rewrite Python source into an instrumented AST and execute it safely."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any, Callable

from pychronicle.instrumentation import instrument_source


Checkpoint = Callable[[int, dict[str, Any]], None]


def _default_checkpoint(line: int, values: dict[str, Any]) -> None:
    """Default checkpoint callback when no callback is provided."""
    return None


def _build_execution_namespace(
    path: Path,
    namespace: dict[str, Any] | None,
    checkpoint: Checkpoint,
) -> dict[str, Any]:
    """Build the namespace used when executing rewritten source."""

    execution_namespace: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(path),
        "__pychronicle_checkpoint__": checkpoint,
    }

    if namespace is not None:
        execution_namespace.update(namespace)

    execution_namespace["__pychronicle_checkpoint__"] = checkpoint

    return execution_namespace


def rewrite_source(
    source: str,
    filename: str | Path = "<memory>",
) -> ast.Module:
    """Parse source code and return its instrumented abstract syntax tree."""

    if not isinstance(source, str):
        raise TypeError("source must be a string")

    tree = instrument_source(source, str(filename))

    if not isinstance(tree, ast.Module):
        raise TypeError("instrument_source must return an ast.Module")

    return tree


def execute_source(
    source: str,
    filename: str | Path = "<memory>",
    checkpoint: Checkpoint | None = None,
    namespace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute an instrumented source program without modifying its original file."""

    path = Path(filename)
    tree = rewrite_source(source, path)
    code = compile(tree, str(path), "exec")

    if checkpoint is None:
        checkpoint = _default_checkpoint

    execution_namespace = _build_execution_namespace(
        path,
        namespace,
        checkpoint,
    )

    source_directory = path.parent.resolve()
    path_entry = str(source_directory)
    path_added = False

    if path != Path("<memory>") and path_entry not in sys.path:
        sys.path.insert(0, path_entry)
        path_added = True

    try:
        exec(code, execution_namespace, execution_namespace)
    finally:
        if path_added:
            sys.path.remove(path_entry)

    return execution_namespace