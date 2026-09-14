import ast

from pychronicle.instrumentation import instrument_source


def test_match_case_assignment_is_instrumented():
    source = """match 1:
    case 1:
        result = "matched"
"""

    tree = instrument_source(source)

    output = ast.unparse(tree)

    assert "__pychronicle_checkpoint__(2, locals())" in output
    assert "__pychronicle_checkpoint__(3, locals())" in output
    assert "result = 'matched'" in output