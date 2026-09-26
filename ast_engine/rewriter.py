"""AST rewriter for executing instrumented Python code."""

from __future__ import annotations

import ast
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
    """Parse and transform Python source into an instrumented AST."""

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
    """Execute transformed Python source without modifying the original source."""

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

    exec(code, execution_namespace, execution_namespace)

    return execution_namespace