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
            # FRAME REQUIRED WHEN NOT USING --list OR --variable
            # ----------------------------------------------------------

            if args.frame is None:
                inspect.error(
                    "--frame is required unless "
                    "--list or --variable is used"
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