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

    inspect = commands.add_parser(
        "inspect",
        help="show reconstructed state from a trace database",
    )

    inspect.add_argument(
        "database",
        type=Path,
    )

    inspect.add_argument(
        "--frame",
        type=int,
        required=True,
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

    args = parser.parse_args()

    if args.command == "inspect":
        store = TraceStore(args.database)

        try:
            if args.event is not None:
                matching_frames = list(
                    store.frames(
                        scope=args.scope,
                        event=args.event,
                    )
                )

                frame_ids = {
                    frame.id
                    for frame in matching_frames
                }

                if args.frame not in frame_ids:
                    print(
                        json.dumps(
                            {},
                            indent=2,
                            ensure_ascii=False,
                            default=str,
                        )
                    )
                    return

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

    if args.tui:
        from .tui import launch

        launch(
            result.store,
            result.filename,
        )


if __name__ == "__main__":
    main()