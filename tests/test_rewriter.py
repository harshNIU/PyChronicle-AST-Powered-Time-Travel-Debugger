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