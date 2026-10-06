# Tracer module

Records what happens while a Python program runs, using `sys.settrace`,
and saves the recording to SQLite so it can be inspected afterwards.

## Files

- `basic_tracer.py` - `ExecutionTracer`, which records calls, line-by-line
  variable changes, returns and exceptions, with source text and an
  optional step limit for long-running code
- `timeline_store.py` - `TimelineStore`, which saves and loads a recording
  using SQLite, and answers queries like "show me every value this
  variable held"
- `run_tracer.py` - command-line tool that traces any Python script
- `query_timeline.py` - command-line tool that filters/searches an
  already-saved timeline
- `export_timeline.py` - command-line tool that exports a saved timeline
  to plain JSON
- `compare_timelines.py` - command-line tool that compares two saved
  timelines (e.g. before/after a code change)

## Trace a script

From the project root:

```
python3 tracer/run_tracer.py examples/tracer_demo.py
```

Options:

- `--db FILE` - where to save the timeline (default: `timeline.db`)
- `--quiet` - save the timeline without printing it
- `--max-steps N` - stop recording after N steps
- `--summary` - print an aggregate summary after the timeline

Exit codes: `0` finished normally, `1` the script raised an error
(the timeline is still saved), `2` script file not found.

## Use it from Python

```python
from basic_tracer import ExecutionTracer

tracer = ExecutionTracer(target_file=__file__, max_steps=5000)
tracer.start()
# ... code to trace ...
tracer.stop()
tracer.print_timeline()
tracer.print_summary()
```

## What gets recorded

Each step is a dict with a `type`:

- `call` - a function was entered
- `line` - a line ran, with the variables that changed
- `return` - a function returned, with its return value
- `exception` - an exception was raised, with its type and message

Every step also carries the literal source text of that line. Values
that can't be printed or compared safely are handled without crashing,
and long values are truncated when saved.

## Step limits for long or infinite loops

Once the limit is hit, recording stops automatically but the traced
program keeps running. Check `tracer.truncated` to see if this happened.

```
python3 tracer/run_tracer.py examples/loop_demo.py --max-steps 30 --summary
```

## Querying a saved timeline

```
python3 tracer/query_timeline.py --db timeline.db --function add_numbers
python3 tracer/query_timeline.py --db timeline.db --exceptions
python3 tracer/query_timeline.py --db timeline.db --summary
```

## Looking up a single variable's history

The core "time travel" question: what was this variable at each point
during the run?

```
python3 tracer/query_timeline.py --db timeline.db --variable total
```

## Exporting a timeline to JSON

```
python3 tracer/export_timeline.py --db timeline.db --pretty
python3 tracer/export_timeline.py --db timeline.db --function add_numbers --out add_numbers.json
```

## Comparing two runs

Trace the same program twice (e.g. before and after a change) into two
separate databases, then compare them:

```
python3 tracer/run_tracer.py your_script.py --db before.db --quiet
python3 tracer/run_tracer.py your_script.py --db after.db --quiet
python3 tracer/compare_timelines.py --old before.db --new after.db
```

## Tests

```
python3 -m pytest tests/test_tracer.py tests/test_run_tracer.py tests/test_tracer_advanced.py tests/test_query_timeline.py tests/test_export_timeline.py tests/test_variable_history.py tests/test_compare_timelines.py -v
```