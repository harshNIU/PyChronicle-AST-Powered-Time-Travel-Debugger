"""Execution engine: AST hooks plus a scoped sys.settrace fallback."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any

from .instrumentation import Assignment, find_assignments, instrument_source
from .storage import TraceStore


@dataclass
class TraceResult:
    store: TraceStore
    assignments: list[Assignment]
    filename: Path


class Chronicle:
    def __init__(self, database: str | Path = ":memory:") -> None:
        self.store = TraceStore(database)
        self._target = ""

    @staticmethod
    def _visible(values: dict[str, Any]) -> dict[str, Any]:
        return {name: value for name, value in values.items() if not name.startswith("__")}

    @staticmethod
    def _scope(frame: FrameType) -> str:
        return f"{frame.f_code.co_name}@{frame.f_code.co_firstlineno}"

    def _capture(self, line: int, values: dict[str, Any], event: str, scope: str = "<module>") -> None:
        self.store.record(line, event, scope, self._visible(dict(values)))

    def _tracer(self, frame: FrameType, event: str, arg: Any):
        if frame.f_code.co_filename != self._target:
            return self._tracer
        if event in {"line", "return", "exception"}:
            self._capture(frame.f_lineno, frame.f_locals, event, self._scope(frame))
        return self._tracer

    def run_file(self, path: str | Path, argv: list[str] | None = None) -> TraceResult:
        target = Path(path).resolve()
        source = target.read_text(encoding="utf-8")
        return self.run_source(source, target, argv)

    def run_source(self, source: str, filename: str | Path = "<memory>", argv: list[str] | None = None) -> TraceResult:
        path = Path(filename).resolve()
        self._target = str(path)
        assignments = find_assignments(source, str(path))
        code = compile(instrument_source(source, str(path)), str(path), "exec")
        def ast_checkpoint(line: int, values: dict[str, Any]) -> None:
            # The hook is called directly by instrumented user code, so its caller
            # is the target frame whose scope must match sys.settrace's scope.
            target_frame = sys._getframe(1)
            self._capture(line, values, "ast", self._scope(target_frame))

        namespace = {
            "__name__": "__main__", "__file__": str(path), "__package__": None,
            "__pychronicle_checkpoint__": ast_checkpoint,
        }
        previous_trace, previous_argv = sys.gettrace(), sys.argv
        sys.argv = [str(path), *(argv or [])]
        try:
            sys.settrace(self._tracer)
            exec(code, namespace, namespace)
        finally:
            sys.settrace(previous_trace)
            sys.argv = previous_argv
            self.store.flush()
        return TraceResult(self.store, assignments, path)
