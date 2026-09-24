"""Tests for the AST parser and rewriter."""

import ast

from ast_engine.parser import (
    BoundaryInfo,
    list_assignments,
    list_boundaries,
    parse_file,
)
from ast_engine.rewriter import execute_source, rewrite_source


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


def test_rewriter_handles_loop():
    """The rewriter should execute a program containing a loop."""

    source = """total = 0
for number in range(3):
    total += number
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["total"] == 3
    assert len(checkpoints) >= 2


def test_rewriter_handles_conditional():
    """The rewriter should execute a program containing a conditional."""

    source = """score = 75

if score >= 50:
    result = "Pass"
else:
    result = "Fail"
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["score"] == 75
    assert namespace["result"] == "Pass"
    assert len(checkpoints) >= 1


def test_rewriter_handles_function():
    """The rewriter should execute a program containing a function."""

    source = """def calculate_total(value):
    result = value + 10
    return result

total = calculate_total(5)
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["total"] == 15
    assert len(checkpoints) >= 2


def test_rewrite_source_returns_transformed_ast():
    """The rewriter should return an instrumented AST."""

    source = """score = 10
score += 5
"""

    tree = rewrite_source(source)

    assert isinstance(tree, ast.Module)
    assert len(tree.body) > 2


def test_execute_source_runs_transformed_code():
    """The rewriter should execute the transformed AST."""

    source = """score = 10
score += 5
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["score"] == 15
    assert len(checkpoints) == 2


def test_execute_source_does_not_modify_original_file(tmp_path):
    """The rewriter should execute transformed code without changing the source file."""

    target = tmp_path / "sample.py"

    source = """score = 10
score += 5
"""

    target.write_text(source, encoding="utf-8")

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    execute_source(
        target.read_text(encoding="utf-8"),
        filename=target,
        checkpoint=checkpoint,
    )

    assert target.read_text(encoding="utf-8") == source
    assert checkpoints
    assert target.exists()


def test_list_assignments_finds_nested_function_assignments(tmp_path):
    """The parser should find assignments inside nested functions."""

    target_file = tmp_path / "nested_function.py"

    target_file.write_text(
        """def outer():
    outer_value = 10

    def inner():
        inner_value = outer_value + 5
        return inner_value

    return inner()
""",
        encoding="utf-8",
    )

    tree = parse_file(target_file)
    assignments = list_assignments(tree)

    assert [
        (item.line_number, item.target, item.node_type)
        for item in assignments
    ] == [
        (2, "outer_value", "Assign"),
        (5, "inner_value", "Assign"),
    ]