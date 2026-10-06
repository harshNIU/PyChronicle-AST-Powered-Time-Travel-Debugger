"""
Compare two saved PyChronicle timelines, e.g. two runs of the same
program before and after a change, and report what differs.

Usage:
    python3 tracer/compare_timelines.py --old before.db --new after.db
"""

import argparse
import os
import sys

from timeline_store import TimelineStore


def call_counts(rows):
    counts = {}
    for row in rows:
        event_type, function_name = row[1], row[2]
        if event_type == "call":
            counts[function_name] = counts.get(function_name, 0) + 1
    return counts


def exception_summaries(rows):
    summaries = []
    for row in rows:
        event_type, function_name, line_number = row[1], row[2], row[4]
        exception_type, exception_message = row[7], row[8]
        if event_type == "exception":
            summaries.append((function_name, line_number, exception_type, exception_message))
    return summaries


def compare(old_rows, new_rows):
    """Return a dict describing differences between two timelines."""
    old_counts = call_counts(old_rows)
    new_counts = call_counts(new_rows)

    all_functions = set(old_counts) | set(new_counts)
    call_count_diffs = {}
    for name in sorted(all_functions):
        old_count = old_counts.get(name, 0)
        new_count = new_counts.get(name, 0)
        if old_count != new_count:
            call_count_diffs[name] = {"old": old_count, "new": new_count}

    old_exceptions = exception_summaries(old_rows)
    new_exceptions = exception_summaries(new_rows)

    return {
        "old_total_steps": len(old_rows),
        "new_total_steps": len(new_rows),
        "call_count_diffs": call_count_diffs,
        "new_exceptions_only": [e for e in new_exceptions if e not in old_exceptions],
        "resolved_exceptions": [e for e in old_exceptions if e not in new_exceptions],
    }


def print_comparison(result):
    print("--- Timeline Comparison ---")
    print(f"Old run: {result['old_total_steps']} steps")
    print(f"New run: {result['new_total_steps']} steps")

    print("\nFunction call count changes:")
    if result["call_count_diffs"]:
        for name, diff in result["call_count_diffs"].items():
            print(f"  {name}: {diff['old']} -> {diff['new']}")
    else:
        print("  (none)")

    print("\nNew exceptions (present in new run, not in old):")
    if result["new_exceptions_only"]:
        for function_name, line_number, exc_type, exc_message in result["new_exceptions_only"]:
            print(f"  {exc_type} in {function_name}() at line {line_number}: {exc_message}")
    else:
        print("  (none)")

    print("\nResolved exceptions (present in old run, gone in new):")
    if result["resolved_exceptions"]:
        for function_name, line_number, exc_type, exc_message in result["resolved_exceptions"]:
            print(f"  {exc_type} in {function_name}() at line {line_number}: {exc_message}")
    else:
        print("  (none)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare two saved PyChronicle timelines.")
    parser.add_argument("--old", required=True, help="path to the baseline timeline database")
    parser.add_argument("--new", required=True, help="path to the timeline database to compare against the baseline")
    args = parser.parse_args(argv)

    for label, path in [("--old", args.old), ("--new", args.new)]:
        if not os.path.exists(path):
            print(f"No database found at '{path}' (from {label}).", file=sys.stderr)
            return 2

    old_store = TimelineStore(args.old)
    try:
        old_rows = old_store.load_history()
    finally:
        old_store.close()

    new_store = TimelineStore(args.new)
    try:
        new_rows = new_store.load_history()
    finally:
        new_store.close()

    print_comparison(compare(old_rows, new_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())