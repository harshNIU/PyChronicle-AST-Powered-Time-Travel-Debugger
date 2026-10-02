"""Tests for the AST rewriter."""

from pathlib import Path

from ast_engine.rewriter import execute_source, rewrite_source


def test_rewrite_source_returns_transformed_ast():
    """The rewriter should return an instrumented AST."""

    source = """score = 10
score += 5
"""

    tree = rewrite_source(source)

    assert tree is not None
    assert hasattr(tree, "body")


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
    assert Path(target).exists()


def test_rewrite_source_rejects_non_string_source():
    """The rewriter should reject source values that are not strings."""

    try:
        rewrite_source(123)
    except TypeError as error:
        assert str(error) == "source must be a string"
    else:
        raise AssertionError("rewrite_source should reject non-string source")


def test_rewrite_source_accepts_path_filename(tmp_path):
    """The rewriter should accept a Path object as the filename."""

    target = tmp_path / "sample.py"

    tree = rewrite_source(
        "score = 10\n",
        filename=target,
    )

    assert tree is not None
    assert hasattr(tree, "body")


def test_execute_source_works_without_custom_checkpoint():
    """The rewriter should use its default checkpoint when none is provided."""

    namespace = execute_source(
        "score = 10\nscore += 5\n",
    )

    assert namespace["score"] == 15


def test_execute_source_checkpoint_captures_updated_values():
    """The rewriter should capture the updated value at each assignment."""

    source = """score = 10
score += 5
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert checkpoints[0][0] == 1
    assert checkpoints[0][1]["score"] == 10

    assert checkpoints[1][0] == 2
    assert checkpoints[1][1]["score"] == 15


def test_execute_source_captures_if_else_values():
    """The rewriter should capture values from an if/else conditional."""

    source = """score = 10
if score > 5:
    score = 20
else:
    score = 0
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["score"] == 20
    assert checkpoints[-1][1]["score"] == 20


def test_execute_source_captures_for_loop_values():
    """The rewriter should capture values while executing a for loop."""

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
    assert checkpoints
    assert checkpoints[-1][1]["total"] == 3


def test_execute_source_supports_imported_module(tmp_path):
    """The rewriter should execute source that imports another Python module."""

    helper = tmp_path / "helper.py"

    helper.write_text(
        """def get_value():
    return 42
""",
        encoding="utf-8",
    )

    source = """from helper import get_value

result = get_value()
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        filename=tmp_path / "main.py",
        checkpoint=checkpoint,
    )

    assert namespace["result"] == 42
    assert checkpoints


def test_execute_source_supports_decorated_function():
    """The rewriter should execute decorated functions correctly."""

    source = """def double_result(function):
    def wrapper(value):
        return function(value) * 2

    return wrapper


@double_result
def calculate(value):
    result = value + 5
    return result


answer = calculate(10)
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["answer"] == 30
    assert checkpoints


def test_execute_source_supports_list_comprehension():
    """The rewriter should execute list comprehensions correctly."""

    source = """numbers = [1, 2, 3, 4]
squares = [number * number for number in numbers]
"""

    checkpoints = []

    def checkpoint(line, values):
        checkpoints.append((line, dict(values)))

    namespace = execute_source(
        source,
        checkpoint=checkpoint,
    )

    assert namespace["squares"] == [1, 4, 9, 16]
    assert checkpoints