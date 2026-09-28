"""AST visitor for collecting variable assignment nodes."""

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class AssignmentInfo:
    """Information about a variable assignment."""

    line_number: int
    column_offset: int
    target: str
    node_type: str


class AssignmentVisitor(ast.NodeVisitor):
    """Visit an AST and collect variable assignment information."""

    def __init__(self) -> None:
        self.assignments: list[AssignmentInfo] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Collect regular assignment statements."""

        for target in node.targets:
            self.assignments.append(
                AssignmentInfo(
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    target=ast.unparse(target),
                    node_type="Assign",
                )
            )

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Collect annotated assignments."""

        self.assignments.append(
            AssignmentInfo(
                line_number=node.lineno,
                column_offset=node.col_offset,
                target=ast.unparse(node.target),
                node_type="AnnAssign",
            )
        )

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Collect augmented assignments such as x += 1."""

        self.assignments.append(
            AssignmentInfo(
                line_number=node.lineno,
                column_offset=node.col_offset,
                target=ast.unparse(node.target),
                node_type="AugAssign",
            )
        )

        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """Collect assignment expressions such as (x := value)."""

        self.assignments.append(
            AssignmentInfo(
                line_number=node.lineno,
                column_offset=node.col_offset,
                target=ast.unparse(node.target),
                node_type="NamedExpr",
            )
        )

        self.generic_visit(node)


def list_assignments(tree: ast.AST) -> list[AssignmentInfo]:
    """Return all variable assignments found in an AST."""

    visitor = AssignmentVisitor()
    visitor.visit(tree)
    return visitor.assignments