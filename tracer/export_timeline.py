"""
Export a saved PyChronicle timeline (see run_tracer.py) to JSON, so other
tools (the team's CLI/TUI, a notebook, anything) can read it without
touching SQLite directly.

Usage:
    python3 tracer/export_timeline.py --db timeline.db
    python3 tracer/export_timeline.py --db timeline.db --function add --pretty
    python3 tracer/export_timeline.py --db timeline.db --out timeline.json
"""

import argparse
import ast
import json
import os
import sys

from timeline_store import TimelineStore


def parse_changed_vars(changed_vars_str):
    """
    TimelineStore saves changed variables as the text of a Python dict
    (e.g. "{'x': '1'}"), which isn't valid JSON on its own. This turns it
    back into a real dict so json.dumps can serialize it properly. If it
    can't be parsed for some reason, the original string is kept as-is
    rather than dropping the data.
    """
    if not changed_vars_str:
        return None
    try:
        return ast.literal_eval(changed_vars_str)
    except (ValueError, SyntaxError):
        return changed_vars_str


def row_to_dict(row):
    """Convert one row from TimelineStore into a JSON-friendly dict."""
    (step_index, event_type, function_name, depth, line_number,
     changed_vars, return_value, exception_type, exception_message, source_text) = row

    return {
        "step_index": step_index,
        "event_type": event_type,
        "function_name": function_name,
        "depth": depth,
        "line_number": line_number,
        "changed_vars": parse_changed_vars(changed_vars),
        "return_value": return_value,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "source_text": source_text,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export a saved PyChronicle timeline to JSON.")
    parser.add_argument("--db", default="timeline.db", help="timeline database to read (default: timeline.db)")
    parser.add_argument("--function", help="export only steps from this function")
    parser.add_argument("--type", choices=["call", "line", "return", "exception"], help="export only steps of this event type")
    parser.add_argument("--out", help="write JSON to this file instead of printing it")
    parser.add_argument("--pretty", action="store_true", help="pretty-print the JSON output")
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"No database found at '{args.db}'. Run tracer/run_tracer.py first.", file=sys.stderr)
        return 2

    store = TimelineStore(args.db)
    try:
        if args.function:
            rows = store.get_steps_by_function(args.function)
        elif args.type:
            rows = store.get_steps_by_type(args.type)
        else:
            rows = store.load_history()
    finally:
        store.close()

    steps = [row_to_dict(row) for row in rows]
    output_text = json.dumps(steps, indent=2 if args.pretty else None)

    if args.out:
        with open(args.out, "w") as f:
            f.write(output_text)
        print(f"Wrote {len(steps)} steps to {args.out}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())