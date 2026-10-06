"""
Query a saved PyChronicle timeline (see run_tracer.py) without rerunning
the traced script.

Usage:
    python3 tracer/query_timeline.py --db timeline.db --function add
    python3 tracer/query_timeline.py --db timeline.db --type exception
    python3 tracer/query_timeline.py --db timeline.db --exceptions
    python3 tracer/query_timeline.py --db timeline.db --summary
    python3 tracer/query_timeline.py --db timeline.db --variable total

Day 17 improvement:
- --variable NAME prints how a single variable's value changed over the
  entire run, in order: the core "time travel" question.
"""

import argparse
import os
import sys

from timeline_store import TimelineStore


def format_row(row):
    (step_index, event_type, function_name, depth, line_number,
     changed_vars, return_value, exception_type, exception_message, source_text) = row

    indent = "    " * max((depth or 1) - 1, 0)
    source = f"  # {source_text}" if source_text else ""

    if event_type == "call":
        return f"[{step_index}] {indent}-> Entering {function_name}() at line {line_number}{source}"
    if event_type == "return":
        return f"[{step_index}] {indent}<- Exiting {function_name}() at line {line_number} -> returned {return_value}{source}"
    if event_type == "exception":
        return f"[{step_index}] {indent}!! Exception in {function_name}() at line {line_number}: {exception_type}: {exception_message}{source}"
    return f"[{step_index}] {indent}Line {line_number} ({function_name}){source} | Changed: {changed_vars}"


def print_summary(rows):
    function_calls = {}
    exceptions = []
    for row in rows:
        event_type, function_name = row[1], row[2]
        if event_type == "call":
            function_calls[function_name] = function_calls.get(function_name, 0) + 1
        elif event_type == "exception":
            exceptions.append(row)

    print(f"Total steps in database: {len(rows)}")
    print("Function calls:")
    for name, count in function_calls.items():
        print(f"  {name}: {count}")
    print(f"Exceptions: {len(exceptions)}")
    for row in exceptions:
        print(f"  {format_row(row)}")


def print_variable_history(history, variable_name):
    if not history:
        print(f"No recorded changes for variable '{variable_name}'.")
        return

    print(f"--- History of '{variable_name}' ---")
    for entry in history:
        source = f"  # {entry['source_text']}" if entry["source_text"] else ""
        print(f"[{entry['step_index']}] {entry['function_name']}() line {entry['line_number']}: "
              f"{variable_name} = {entry['value']}{source}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Query a saved PyChronicle timeline.")
    parser.add_argument("--db", default="timeline.db", help="timeline database to read (default: timeline.db)")
    parser.add_argument("--function", help="show only steps from this function")
    parser.add_argument("--type", choices=["call", "line", "return", "exception"], help="show only steps of this event type")
    parser.add_argument("--exceptions", action="store_true", help="shortcut for --type exception")
    parser.add_argument("--summary", action="store_true", help="print an aggregate summary instead of individual steps")
    parser.add_argument("--variable", help="show how this variable's value changed over the whole run")
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"No database found at '{args.db}'. Run tracer/run_tracer.py first.", file=sys.stderr)
        return 2

    store = TimelineStore(args.db)
    try:
        if args.variable:
            history = store.get_variable_history(args.variable)
            print_variable_history(history, args.variable)
            return 0

        if args.function:
            rows = store.get_steps_by_function(args.function)
        elif args.exceptions or args.type == "exception":
            rows = store.get_exceptions()
        elif args.type:
            rows = store.get_steps_by_type(args.type)
        else:
            rows = store.load_history()
    finally:
        store.close()

    if not rows:
        print("No matching steps found.")
        return 0

    if args.summary:
        print_summary(rows)
    else:
        for row in rows:
            print(format_row(row))

    return 0


if __name__ == "__main__":
    sys.exit(main())