"""AST analysis and non-destructive checkpoint injection."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    line_number: int
    names: tuple[str, ...]
    kind: str


def _names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in _names(item)]
    return []


class AssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assignments: list[Assignment] = []

    def _add(self, node: ast.AST, targets: list[ast.AST], kind: str) -> None:
        names = tuple(name for target in targets for name in _names(target))
        if names:
            self.assignments.append(Assignment(node.lineno, names, kind))

    def visit_Assign(self, node: ast.Assign) -> None:
        self._add(node, node.targets, "assign"); self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._add(node, [node.target], "annotated"); self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._add(node, [node.target], "augmented"); self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._add(node, [node.target], "loop"); self.generic_visit(node)


def find_assignments(source: str, filename: str = "<unknown>") -> list[Assignment]:
    tree = ast.parse(source, filename=filename)
    collector = AssignmentCollector(); collector.visit(tree)
    return collector.assignments


class CheckpointInjector(ast.NodeTransformer):
    """Append a hook after ordinary statements in every executable body."""
    excluded = (ast.Return, ast.Raise, ast.Break, ast.Continue, ast.Import, ast.ImportFrom)

    def _hook(self, statement: ast.stmt) -> ast.Expr:
        call = ast.Call(
            func=ast.Name(id="__pychronicle_checkpoint__", ctx=ast.Load()),
            args=[ast.Constant(statement.lineno), ast.Call(func=ast.Name(id="locals", ctx=ast.Load()), args=[], keywords=[])],
            keywords=[],
        )
        # Copy both start and end locations from a real statement: manually setting
        # only ``lineno`` creates an invalid (end before start) AST on Python 3.11+.
        return ast.copy_location(ast.Expr(value=call), statement)

    def _body(self, statements: list[ast.stmt]) -> list[ast.stmt]:
        output: list[ast.stmt] = []
        for statement in statements:
            rewritten = self.visit(statement)
            nodes = rewritten if isinstance(rewritten, list) else [rewritten]
            output.extend(nodes)
            if isinstance(statement, ast.stmt) and not isinstance(statement, self.excluded):
                output.append(self._hook(statement))
        return output

    def visit_Module(self, node: ast.Module) -> ast.Module:
        node.body = self._body(node.body); return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.body = self._body(node.body); return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node.body = self._body(node.body); return node

    def visit_If(self, node: ast.If) -> ast.If:
        node.body = self._body(node.body); node.orelse = self._body(node.orelse); return node

    def visit_For(self, node: ast.For) -> ast.For:
        node.body = self._body(node.body); node.orelse = self._body(node.orelse); return node

    visit_AsyncFor = visit_For

    def visit_While(self, node: ast.While) -> ast.While:
        node.body = self._body(node.body); node.orelse = self._body(node.orelse); return node

    def visit_With(self, node: ast.With) -> ast.With:
        node.body = self._body(node.body); return node

    visit_AsyncWith = visit_With

    def visit_Try(self, node: ast.Try) -> ast.Try:
        node.body = self._body(node.body); node.orelse = self._body(node.orelse); node.finalbody = self._body(node.finalbody)
        for handler in node.handlers: handler.body = self._body(handler.body)
        return node


def instrument_source(source: str, filename: str = "<unknown>") -> ast.Module:
    tree = ast.parse(source, filename=filename)
    tree = CheckpointInjector().visit(tree)
    return ast.fix_missing_locations(tree)
