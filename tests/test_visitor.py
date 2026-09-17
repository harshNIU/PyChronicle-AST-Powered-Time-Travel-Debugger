"""Tests for the AST assignment visitor."""

import ast

from ast_engine.visitor import (
    AssignmentInfo,
    AssignmentVisitor,
    list_assignments,
)


def test_assignment_visitor_finds_assignments():
    """The visitor should find different types of assignments."""

    source = """score = 10
name: str = "PyChronicle"
score += 1

def update():
    inner_value = score
    return inner_value

if (matched_score := score) > 0:
    print(matched_score)
"""

    tree = ast.parse(source)

    assignments = list_assignments(tree)

    assert assignments == [
        AssignmentInfo(
            line_number=1,
            column_offset=0,
            target="score",
            node_type="Assign",
        ),
        AssignmentInfo(
            line_number=2,
            column_offset=0,
            target="name",
            node_type="AnnAssign",
        ),
        AssignmentInfo(
            line_number=3,
            column_offset=0,
            target="score",
            node_type="AugAssign",
        ),
        AssignmentInfo(
            line_number=6,
            column_offset=4,
            target="inner_value",
            node_type="Assign",
        ),
        AssignmentInfo(
            line_number=9,
            column_offset=4,
            target="matched_score",
            node_type="NamedExpr",
        ),
    ]


def test_assignment_visitor_is_node_visitor():
    """AssignmentVisitor should extend ast.NodeVisitor."""

    assert issubclass(AssignmentVisitor, ast.NodeVisitor)