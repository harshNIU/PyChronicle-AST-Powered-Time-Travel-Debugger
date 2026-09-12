"""Delta-oriented SQLite persistence and state reconstruction."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


@dataclass(frozen=True)
class Frame:
    id: int
    timestamp_ns: int
    line_number: int
    event: str
    scope: str


class TraceStore:
    """Store only changed values; reconstruct a frame by replaying its deltas."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row
        self._last: dict[tuple[str, str], str] = {}
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode = MEMORY;
            PRAGMA synchronous = OFF;
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY, timestamp_ns INTEGER NOT NULL,
                line_number INTEGER NOT NULL, event TEXT NOT NULL, scope TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS changes (
                frame_id INTEGER NOT NULL REFERENCES frames(id), scope TEXT NOT NULL,
                variable_name TEXT NOT NULL, value_json TEXT, operation TEXT NOT NULL,
                PRIMARY KEY (frame_id, scope, variable_name)
            );
            CREATE INDEX IF NOT EXISTS changes_frame ON changes(frame_id);
            CREATE INDEX IF NOT EXISTS changes_name ON changes(variable_name, frame_id);
            """
        )

    @staticmethod
    def serialize(value: Any) -> str:
        """Produce stable, readable JSON without failing on arbitrary Python objects."""
        try:
            return json.dumps(value, sort_keys=True, default=repr, ensure_ascii=False)
        except (TypeError, ValueError, OverflowError):
            return json.dumps(repr(value), ensure_ascii=False)

    def record(self, line_number: int, event: str, scope: str, values: dict[str, Any]) -> int | None:
        encoded = {name: self.serialize(value) for name, value in values.items()}
        prior_names = {name for candidate_scope, name in self._last if candidate_scope == scope}
        changes: list[tuple[str, str | None, str]] = []
        for name, value in encoded.items():
            if self._last.get((scope, name)) != value:
                changes.append((name, value, "set"))
        for name in prior_names - encoded.keys():
            changes.append((name, None, "delete"))
        if not changes:
            return None
        cursor = self.connection.execute(
            "INSERT INTO frames(timestamp_ns, line_number, event, scope) VALUES (?, ?, ?, ?)",
            (time.time_ns(), line_number, event, scope),
        )
        frame_id = int(cursor.lastrowid)
        self.connection.executemany(
            "INSERT INTO changes(frame_id, scope, variable_name, value_json, operation) VALUES (?, ?, ?, ?, ?)",
            [(frame_id, scope, name, value, operation) for name, value, operation in changes],
        )
        for name, value, operation in changes:
            key = (scope, name)
            if operation == "delete":
                self._last.pop(key, None)
            else:
                self._last[key] = value or "null"
        return frame_id

    def frames(self) -> Iterator[Frame]:
        rows = self.connection.execute("SELECT * FROM frames ORDER BY id")
        yield from (Frame(**dict(row)) for row in rows)

    def frame_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM frames").fetchone()[0])

    def state_at(self, frame_id: int, scope: str | None = None) -> dict[str, Any]:
        sql = "SELECT scope, variable_name, value_json, operation FROM changes WHERE frame_id <= ?"
        args: list[Any] = [frame_id]
        if scope is not None:
            sql += " AND (scope = ? OR scope LIKE ?)"
            args.extend([scope, f"{scope}@%"])
        sql += " ORDER BY frame_id, rowid"
        state: dict[str, Any] = {}
        for row in self.connection.execute(sql, args):
            name = row["variable_name"] if scope else f"{row['scope']}::{row['variable_name']}"
            if row["operation"] == "delete":
                state.pop(name, None)
            else:
                state[name] = json.loads(row["value_json"])
        return state

    def changes_for(self, variable_name: str) -> list[sqlite3.Row]:
        return list(self.connection.execute(
            """SELECT f.id, f.line_number, f.event, c.scope, c.value_json, c.operation
               FROM changes c JOIN frames f ON f.id = c.frame_id
               WHERE c.variable_name = ? ORDER BY f.id""", (variable_name,)
        ))

    def flush(self) -> None:
        """Make a file-backed timeline available to another CLI invocation."""
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
