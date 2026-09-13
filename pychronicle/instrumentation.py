import ast
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Assignment:
    """
    Stores information about one assignment.
    """

    kind: str
    names: tuple[str, ...]


class AssignmentCollector(ast.NodeVisitor):
    """
    Collect assignment information from Python source code.
    """

    def __init__(self):
        self.assignments: list[Assignment] = []

    def visit_Assign(self, node: ast.Assign):
        names = self._collect_target_names(node.targets)

        if names:
            self.assignments.append(
                Assignment(
                    kind="assign",
                    names=tuple(names),
                )
            )

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        names = self._collect_target_names([node.target])

        if names:
            self.assignments.append(
                Assignment(
                    kind="assign",
                    names=tuple(names),
                )
            )

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        names = self._collect_target_names([node.target])

        if names:
            self.assignments.append(
                Assignment(
                    kind="augmented",
                    names=tuple(names),
                )
            )

        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        names = self._collect_target_names([node.target])

        if names:
            self.assignments.append(
                Assignment(
                    kind="loop",
                    names=tuple(names),
                )
            )

        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        names = self._collect_target_names([node.target])

        if names:
            self.assignments.append(
                Assignment(
                    kind="loop",
                    names=tuple(names),
                )
            )

        self.generic_visit(node)

    def _collect_target_names(self, targets):
        names = []

        for target in targets:
            self._collect_target(target, names)

        return names

    def _collect_target(self, target, names):
        if isinstance(target, ast.Name):
            names.append(target.id)

        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._collect_target(element, names)

        elif isinstance(target, ast.Starred):
            self._collect_target(target.value, names)


def find_assignments(
    source: str,
    filename: Optional[str] = None,
):
    """
    Find assignments in Python source code.
    """

    if not isinstance(source, str):
        raise TypeError("source must be a string")

    tree = ast.parse(
        source,
        filename=filename or "<memory>",
    )

    collector = AssignmentCollector()
    collector.visit(tree)

    return collector.assignments


class InstrumentationTransformer(ast.NodeTransformer):
    """
    Adds checkpoint calls after assignments and
    inside match-case blocks.
    """

    CHECKPOINT_NAME = "__pychronicle_checkpoint__"

    def _checkpoint(self, lineno):
        """
        Create:

            __pychronicle_checkpoint__(lineno, locals())
        """

        call = ast.Call(
            func=ast.Name(
                id=self.CHECKPOINT_NAME,
                ctx=ast.Load(),
            ),
            args=[
                ast.Constant(value=lineno),
                ast.Call(
                    func=ast.Name(
                        id="locals",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                ),
            ],
            keywords=[],
        )

        checkpoint = ast.Expr(value=call)

        end_col = len(
            f"{self.CHECKPOINT_NAME}({lineno}, locals())"
        )

        checkpoint.lineno = lineno
        checkpoint.col_offset = 0
        checkpoint.end_lineno = lineno
        checkpoint.end_col_offset = end_col

        call.lineno = lineno
        call.col_offset = 0
        call.end_lineno = lineno
        call.end_col_offset = end_col

        return checkpoint

    def visit_Assign(self, node):
        node = self.generic_visit(node)

        checkpoint = self._checkpoint(node.lineno)

        return [node, checkpoint]

    def visit_AnnAssign(self, node):
        node = self.generic_visit(node)

        checkpoint = self._checkpoint(node.lineno)

        return [node, checkpoint]

    def visit_AugAssign(self, node):
        node = self.generic_visit(node)

        checkpoint = self._checkpoint(node.lineno)

        return [node, checkpoint]

    def visit_If(self, node):
        self.generic_visit(node)
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        return node

    def visit_AsyncFor(self, node):
        self.generic_visit(node)
        return node

    def visit_While(self, node):
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        return node

    def visit_Match(self, node):
        self.generic_visit(node)

        for case in node.cases:
            if not case.body:
                continue

            lineno = self._get_case_lineno(case)

            if lineno is None:
                continue

            checkpoint = self._checkpoint(lineno)

            case.body.insert(0, checkpoint)

        return node

    def _get_case_lineno(self, case):
        pattern = getattr(case, "pattern", None)

        if pattern is not None:
            lineno = getattr(pattern, "lineno", None)

            if lineno is not None:
                return lineno

        guard = getattr(case, "guard", None)

        if guard is not None:
            lineno = getattr(guard, "lineno", None)

            if lineno is not None:
                return lineno

        if case.body:
            first_statement = case.body[0]

            lineno = getattr(
                first_statement,
                "lineno",
                None,
            )

            if lineno is not None:
                return lineno

        return None


def instrument_source(
    source: str,
    filename: Optional[str] = None,
):
    """
    Parse and instrument Python source code.
    """

    if not isinstance(source, str):
        raise TypeError("source must be a string")

    tree = ast.parse(
        source,
        filename=filename or "<memory>",
    )

    transformer = InstrumentationTransformer()

    tree = transformer.visit(tree)

    tree = ast.fix_missing_locations(tree)

    return tree