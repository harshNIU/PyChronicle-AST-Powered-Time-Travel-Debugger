import ast

from pychronicle.instrumentation import instrument_source


def test_instrumentation_adds_checkpoint_after_assignment():
    source = "x = 10\n"

    tree = instrument_source(source)
    output = ast.unparse(tree)

    assert "__pychronicle_checkpoint__(1, locals())" in output


def test_instrumentation_adds_checkpoint_inside_if():
    source = """
x = 10
if x > 5:
    y = 20
"""

    tree = instrument_source(source)
    output = ast.unparse(tree)

    assert "__pychronicle_checkpoint__(4, locals())" in output


def test_instrumentation_adds_checkpoint_inside_match_case():
    source = """
match 1:
    case 1:
        result = "matched"
"""

    tree = instrument_source(source)
    output = ast.unparse(tree)

    assert "__pychronicle_checkpoint__(3, locals())" in output