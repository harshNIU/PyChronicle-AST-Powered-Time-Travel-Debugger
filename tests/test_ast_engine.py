"""Tests for the Day 2 AST parser."""

import ast

from ast_engine.parser import (
    AssignmentInfo,
    BoundaryInfo,
    list_assignments,
    list_boundaries,
    parse_file,
)


def test_parse_file_returns_module_tree(tmp_path):
    """The parser should return an AST module for a Python file."""

    target_file = tmp_path / "sample_program.py"
    target_file.write_text(
        "score = 10\n",
        encoding="utf-8",
    )

    tree = parse_file(target_file)

    assert isinstance(tree, ast.Module)


def test_list_assignments_finds_assignment_nodes(tmp_path):
    """The parser should find assignment nodes throughout the source file."""

    target_file = tmp_path / "sample_program.py"

    target_file.write_text(
        """score = 10
name: str = "PyChronicle"
score += 1
left, right = 1, 2

def update():
    inner_value = score
    return inner_value

if (matched_score := score) > 0:
    print(matched_score)
""",
        encoding="utf-8",
    )

    tree = parse_file(target_file)
    assignments = list_assignments(tree)

    assert [
        (item.line_number, item.column_offset, item.target, item.node_type)
        for item in assignments
    ] == [
        (1, 0, "score", "Assign"),
        (2, 0, "name", "AnnAssign"),
        (3, 0, "score", "AugAssign"),
        (4, 0, "(left, right)", "Assign"),
        (7, 4, "inner_value", "Assign"),
        (10, 4, "matched_score", "NamedExpr"),
    ]


def test_list_boundaries_finds_functions_and_loops():
    """The parser should find function and loop boundaries."""

    source = """def calculate():
    for item in items:
        while item:
            item = None
"""

    tree = ast.parse(source)

    boundaries = list_boundaries(tree)

    assert boundaries == [
        BoundaryInfo(
            line_number=1,
            boundary_type="function",
            name="calculate",
        ),
        BoundaryInfo(
            line_number=2,
            boundary_type="loop",
            name="For",
        ),
        BoundaryInfo(
            line_number=3,
            boundary_type="loop",
            name="While",
        ),
    ]