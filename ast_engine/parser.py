"""Utilities for parsing Python source files and finding AST boundaries."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssignmentInfo:
    """A simplified description of one assignment expression in source code."""

    line_number: int
    target: str
    node_type: str


@dataclass(frozen=True)
class BoundaryInfo:
    """A simplified description of a function or loop boundary."""

    line_number: int
    boundary_type: str
    name: str


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
            target_nodes = node.targets

        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            target_nodes = [node.target]

        else:
            continue

        for target_node in target_nodes:
            assignments.append(
                AssignmentInfo(
                    line_number=node.lineno,
                    target=ast.unparse(target_node),
                    node_type=type(node).__name__,
                )
            )

    return sorted(
        assignments,
        key=lambda item: (item.line_number, item.target),
    )


def list_boundaries(tree: ast.AST) -> list[BoundaryInfo]:
    """Return function and loop boundaries used for hook injection planning."""

    boundaries: list[BoundaryInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            boundaries.append(
                BoundaryInfo(
                    line_number=node.lineno,
                    boundary_type="function",
                    name=node.name,
                )
            )

        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            boundaries.append(
                BoundaryInfo(
                    line_number=node.lineno,
                    boundary_type="loop",
                    name=type(node).__name__,
                )
            )

    return sorted(
        boundaries,
        key=lambda item: (item.line_number, item.boundary_type, item.name),
    )