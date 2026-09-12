"""Runtime hook made available only to the instrumented program namespace."""

from __future__ import annotations

from typing import Any, Callable


def checkpoint(callback: Callable[[int, dict[str, Any], str], None], line: int, namespace: dict[str, Any]) -> None:
    """Capture after an AST-rewritten statement has completed."""
    callback(line, namespace, "ast")
