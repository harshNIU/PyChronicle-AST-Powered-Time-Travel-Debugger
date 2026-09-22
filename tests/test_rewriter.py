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