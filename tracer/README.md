# Tracer module

Records what happens while a Python program runs, using `sys.settrace`,
and saves the recording to SQLite so it can be inspected afterwards.

## Files

- `basic_tracer.py` - `ExecutionTracer`, which records calls, line-by-line
  variable changes, returns and exceptions
- `timeline_store.py` - `TimelineStore`, which saves and loads a recording
  using SQLite
- `run_tracer.py` - command-line tool that traces any Python script

## Trace a script

From the project root:

```
python3 tracer/run_tracer.py examples/tracer_demo.py
```

Options:

- `--db FILE` - where to save the timeline (default: `timeline.db`)
- `--quiet` - save the timeline without printing it

Exit codes: `0` finished normally, `1` the script raised an error
(the timeline is still saved), `2` script file not found.

## Use it from Python

```python
from basic_tracer import ExecutionTracer

tracer = ExecutionTracer(target_file=__file__)
tracer.start()
# ... code to trace ...
tracer.stop()
tracer.print_timeline()
```

## What gets recorded

Each step is a dict with a `type`:

- `call` - a function was entered
- `line` - a line ran, with the variables that changed
- `return` - a function returned, with its return value
- `exception` - an exception was raised, with its type and message

Values that can't be printed or compared safely are handled without
crashing, and long values are truncated when saved.

## Tests

```
python3 -m pytest tests/test_tracer.py tests/test_run_tracer.py -v
```