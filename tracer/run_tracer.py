"""
Trace any Python script and save its execution timeline.

Usage:
    python3 tracer/run_tracer.py path/to/script.py
    python3 tracer/run_tracer.py path/to/script.py --db my_timeline.db --quiet

Exit codes: 0 = script finished, 1 = script raised an error,
2 = script file not found.
"""

import argparse
import os
import runpy
import sys

from basic_tracer import ExecutionTracer
from timeline_store import TimelineStore


def trace_script(script_path, db_path="timeline.db"):
    """
    Run the script at script_path under the tracer and save the timeline.

    Returns (tracer, error). error is the exception the script stopped
    with, or None if it finished normally. Raises FileNotFoundError if
    the script doesn't exist.
    """
    script_path = os.path.abspath(script_path)
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    tracer = ExecutionTracer(target_file=script_path)

    old_argv = sys.argv
    old_path = list(sys.path)
    sys.argv = [script_path]
    sys.path.insert(0, os.path.dirname(script_path))

    error = None
    tracer.start()
    try:
        runpy.run_path(script_path, run_name="__main__")
    except SystemExit:
        pass
    except Exception as exc:
        error = exc
    finally:
        tracer.stop()
        sys.argv = old_argv
        sys.path[:] = old_path

    store = TimelineStore(db_path)
    try:
        store.clear()
        store.save_history(tracer.history)
    finally:
        store.close()

    return tracer, error


def main(argv=None):
    """Command-line entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(
        description="Trace a Python script and save its execution timeline."
    )
    parser.add_argument("script", help="path to the Python file to trace")
    parser.add_argument(
        "--db",
        default="timeline.db",
        help="SQLite file to save the timeline to (default: timeline.db)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="don't print the timeline, only save it",
    )
    args = parser.parse_args(argv)

    try:
        tracer, error = trace_script(args.script, db_path=args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2

    if not args.quiet:
        tracer.print_timeline()

    print(f"\nSaved {len(tracer.history)} steps to {args.db}")

    if error is not None:
        print(f"The traced script stopped with {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())