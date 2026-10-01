from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import Chronicle
from .storage import TraceStore


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

            if args.variable is not None:
                changes = store.changes_for(args.variable)

                # Apply scope filtering.
                if args.scope is not None:
                    changes = [
                        change
                        for change in changes
                        if (
                            change["scope"] == args.scope
                            or change["scope"].startswith(
                                f"{args.scope}@"
                            )
                        )
                    ]

                # Apply event filtering.
                if args.event is not None:
                    changes = [
                        change
                        for change in changes
                        if change["event"] == args.event
                    ]

                if not changes:
                    print(
                        f"No history found for variable "
                        f"'{args.variable}'."
                    )
                    return

                print(f"Variable: {args.variable}")

                for change in changes:
                    print(
                        f"Frame {change['id']}: "
                        f"line={change['line_number']}, "
                        f"event={change['event']}, "
                        f"scope={change['scope']}, "
                        f"value={change['value_json']}, "
                        f"operation={change['operation']}"
                    )

                return

            # ----------------------------------------------------------
            # FRAME DIFF
            # ----------------------------------------------------------

            if args.diff is not None:
                from_frame, to_frame = args.diff

                if from_frame > to_frame:
                    inspect.error(
                        "FROM frame must be less than or equal to TO frame"
                    )

                before = store.state_at(
                    from_frame,
                    args.scope,
                )

                after = store.state_at(
                    to_frame,
                    args.scope,
                )

                added = {}
                removed = {}
                changed = {}

                all_names = set(before) | set(after)

                for name in sorted(all_names):
                    if name not in before:
                        added[name] = after[name]
                    elif name not in after:
                        removed[name] = before[name]
                    elif before[name] != after[name]:
                        changed[name] = {
                            "from": before[name],
                            "to": after[name],
                        }

                print(
                    f"Changes from Frame "
                    f"{from_frame} -> Frame {to_frame}"
                )

                if not added and not removed and not changed:
                    print("No changes.")
                    return

                if added:
                    print("\nAdded:")
                    for name, value in added.items():
                        print(
                            f"  + {name} = "
                            f"{json.dumps(value, default=str)}"
                        )

                if removed:
                    print("\nRemoved:")
                    for name, value in removed.items():
                        print(
                            f"  - {name} = "
                            f"{json.dumps(value, default=str)}"
                        )

                if changed:
                    print("\nChanged:")
                    for name, values in changed.items():
                        print(
                            f"  ~ {name}: "
                            f"{json.dumps(values['from'], default=str)} "
                            f"-> "
                            f"{json.dumps(values['to'], default=str)}"
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
                    "--list, --variable, or --diff is used"
                )

            # ----------------------------------------------------------
            # EVENT FILTER
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