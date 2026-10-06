from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import Chronicle
from .storage import TraceStore


def format_value(value: object) -> str:
    """Format a value safely for CLI output."""
    return str(value)


def print_timeline(store: TraceStore, scope: str | None, event: str | None) -> None:
    """Print the recorded execution timeline."""
    frames = list(
        store.frames(
            scope=scope,
            event=event,
        )
    )

    print("PyChronicle Timeline")
    print("=" * 72)

    if not frames:
        print("No frames found.")
        return

    for frame in frames:
        print(
            f"Frame {frame.id} | "
            f"line={frame.line_number} | "
            f"event={frame.event} | "
            f"scope={frame.scope}"
        )


def print_variable_history(
    store: TraceStore,
    variable: str,
    scope: str | None,
    event: str | None,
) -> None:
    """Print the recorded history of one variable."""
    changes = store.changes_for(variable)

    if scope is not None:
        changes = [
            change
            for change in changes
            if (
                change["scope"] == scope
                or change["scope"].startswith(f"{scope}@")
            )
        ]

    if event is not None:
        changes = [
            change
            for change in changes
            if change["event"] == event
        ]

    print(f"PyChronicle Variable History: {variable}")
    print("=" * 72)

    if not changes:
        print(f"No history found for variable '{variable}'.")
        return

    for change in changes:
        print(
            f"Frame {change['id']} | "
            f"line={change['line_number']} | "
            f"event={change['event']} | "
            f"scope={change['scope']}"
        )
        print(
            f"  {variable} = {change['value_json']} "
            f"(operation={change['operation']})"
        )


def print_state_history(
    store: TraceStore,
    variable: str | None,
    scope: str | None,
    event: str | None,
) -> None:
    """Print reconstructed state at every recorded frame."""
    frames = list(
        store.frames(
            scope=scope,
            event=event,
        )
    )

    print("PyChronicle State History")
    print("=" * 72)

    if not frames:
        print("No frames found.")
        return

    for frame in frames:
        state = store.state_at(
            frame.id,
            scope,
        )

        if variable is not None:
            matching = {
                key: value
                for key, value in state.items()
                if (
                    key == variable
                    or key.endswith(f"::{variable}")
                    or key.startswith(f"{variable}::")
                )
            }

            if not matching:
                continue

            state = matching

        print()
        print(
            f"Frame {frame.id} | "
            f"line={frame.line_number} | "
            f"event={frame.event} | "
            f"scope={frame.scope}"
        )

        for key, value in state.items():
            print(f"  {key} = {format_value(value)}")


def print_frame_diff(
    store: TraceStore,
    from_frame: int,
    to_frame: int,
    scope: str | None,
) -> None:
    """Print the state differences between two frames."""
    before = store.state_at(
        from_frame,
        scope,
    )

    after = store.state_at(
        to_frame,
        scope,
    )

    added = {
        key: after[key]
        for key in after.keys() - before.keys()
    }

    removed = {
        key: before[key]
        for key in before.keys() - after.keys()
    }

    changed = {
        key: (before[key], after[key])
        for key in before.keys() & after.keys()
        if before[key] != after[key]
    }

    print(
        f"Changes from Frame {from_frame} -> Frame {to_frame}"
    )

    if not added and not removed and not changed:
        print()
        print("No changes.")
        return

    if added:
        print()
        print("Added:")
        for key, value in sorted(added.items()):
            print(f"  + {key} = {format_value(value)}")

    if removed:
        print()
        print("Removed:")
        for key, value in sorted(removed.items()):
            print(f"  - {key} = {format_value(value)}")

    if changed:
        print()
        print("Changed:")
        for key, (old_value, new_value) in sorted(changed.items()):
            print(
                f"  ~ {key}: "
                f"{format_value(old_value)} -> "
                f"{format_value(new_value)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pychronicle",
        description="Record and replay Python variable history.",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ------------------------------------------------------------------
    # RUN COMMAND
    # ------------------------------------------------------------------

    run = commands.add_parser(
        "run",
        help="instrument and execute a script",
    )

    run.add_argument(
        "script",
        type=Path,
    )

    run.add_argument(
        "script_args",
        nargs="*",
        help="arguments for the script",
    )

    run.add_argument(
        "--db",
        default=":memory:",
        help="SQLite file, or :memory: (default)",
    )

    run.add_argument(
        "--tui",
        action="store_true",
        help="open the interactive Textual timeline",
    )

    # ------------------------------------------------------------------
    # INSPECT COMMAND
    # ------------------------------------------------------------------

    inspect = commands.add_parser(
        "inspect",
        help="inspect a trace database",
    )

    inspect.add_argument(
        "database",
        type=Path,
    )

    inspect.add_argument(
        "--frame",
        type=int,
        help="frame ID to inspect",
    )

    inspect.add_argument(
        "--scope",
        help="filter state reconstruction by scope",
    )

    inspect.add_argument(
        "--event",
        help="filter frames by event type",
    )

    inspect.add_argument(
        "--list",
        action="store_true",
        help="list recorded frames",
    )

    inspect.add_argument(
        "--variable",
        help="show recorded history for a variable",
    )

    inspect.add_argument(
        "--diff",
        nargs=2,
        type=int,
        metavar=("FROM", "TO"),
        help="show variable changes between two frames",
    )

    inspect.add_argument(
        "--timeline",
        action="store_true",
        help="show execution timeline",
    )

    inspect.add_argument(
        "--history",
        action="store_true",
        help="show reconstructed state at every frame",
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # INSPECT COMMAND
    # ------------------------------------------------------------------

    if args.command == "inspect":
        store = TraceStore(args.database)

        try:
            # ----------------------------------------------------------
            # VARIABLE HISTORY
            # ----------------------------------------------------------

            if args.variable is not None and not args.history:
                print_variable_history(
                    store,
                    args.variable,
                    args.scope,
                    args.event,
                )
                return

            # ----------------------------------------------------------
            # FRAME DIFF
            # ----------------------------------------------------------

            if args.diff is not None:
                from_frame, to_frame = args.diff

                print_frame_diff(
                    store,
                    from_frame,
                    to_frame,
                    args.scope,
                )
                return

            # ----------------------------------------------------------
            # TIMELINE
            # ----------------------------------------------------------

            if args.timeline:
                print_timeline(
                    store,
                    args.scope,
                    args.event,
                )
                return

            # ----------------------------------------------------------
            # STATE HISTORY
            # ----------------------------------------------------------

            if args.history:
                print_state_history(
                    store,
                    args.variable,
                    args.scope,
                    args.event,
                )
                return

            # ----------------------------------------------------------
            # GET FILTERED FRAMES
            # ----------------------------------------------------------

            frames = list(
                store.frames(
                    scope=args.scope,
                    event=args.event,
                )
            )

            # ----------------------------------------------------------
            # LIST FRAMES
            # ----------------------------------------------------------

            if args.list:
                if not frames:
                    print("No frames found.")
                    return

                for frame in frames:
                    print(
                        f"Frame {frame.id}: "
                        f"line={frame.line_number}, "
                        f"event={frame.event}, "
                        f"scope={frame.scope}"
                    )

                return

            # ----------------------------------------------------------
            # FRAME REQUIRED
            # ----------------------------------------------------------

            if args.frame is None:
                inspect.error(
                    "--frame is required unless "
                    "--list, --variable, --diff, "
                    "--timeline, or --history is used"
                )

            # ----------------------------------------------------------
            # EVENT FILTER VALIDATION
            # ----------------------------------------------------------

            if args.event is not None:
                matching_frame_ids = {
                    frame.id
                    for frame in frames
                }

                if args.frame not in matching_frame_ids:
                    print(
                        json.dumps(
                            {},
                            indent=2,
                            ensure_ascii=False,
                            default=str,
                        )
                    )
                    return

            # ----------------------------------------------------------
            # RECONSTRUCT STATE
            # ----------------------------------------------------------

            state = store.state_at(
                args.frame,
                args.scope,
            )

            print(
                json.dumps(
                    state,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
            )

        finally:
            store.close()

        return

    # ------------------------------------------------------------------
    # RUN SCRIPT
    # ------------------------------------------------------------------

    result = Chronicle(args.db).run_file(
        args.script,
        args.script_args,
    )

    print(
        f"Recorded "
        f"{result.store.frame_count()} "
        f"delta frames from "
        f"{result.filename.name}."
    )

    # ------------------------------------------------------------------
    # TUI
    # ------------------------------------------------------------------

    if args.tui:
        from .tui import launch

        launch(
            result.store,
            result.filename,
        )


if __name__ == "__main__":
    main()