"""Utilities for parsing Python source files and finding assignment nodes."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssignmentInfo:
    """A simplified description of one assignment expression in source code."""

    line_number: int
    column_offset: int
    target: str
    node_type: str


def parse_file(file_path: str | Path) -> ast.Module:
    """Read a Python file and return its parsed abstract syntax tree."""

    path = Path(file_path)
    source_code = path.read_text(encoding="utf-8")
    return ast.parse(source_code, filename=str(path))


def list_assignments(tree: ast.AST) -> list[AssignmentInfo]:
    """Return assignment nodes found anywhere in an abstract syntax tree."""

    assignment_types = (
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.NamedExpr,
    )

    assignments: list[AssignmentInfo] = []

    for node in ast.walk(tree):
        if not isinstance(node, assignment_types):
            continue

        if isinstance(node, ast.Assign):
            # Normal assignment: x = 10
            # ast.Assign stores targets in a list.
            target_nodes = node.targets

        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            # These assignment types have a single target.
            target_nodes = [node.target]

        else:
            continue

        for target_node in target_nodes:
            assignments.append(
                AssignmentInfo(
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    target=ast.unparse(target_node),
                    node_type=type(node).__name__,
                )
            )
            

    return sorted(
        assignments,
        key=lambda item: (item.line_number, item.target),
    )