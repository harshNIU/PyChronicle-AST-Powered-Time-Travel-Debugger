# PyChronicle - AST-Powered Time-Travel Debugger

PyChronicle is a Python time-travel execution tracer. It will use Python's `ast` module and `sys.settrace` to record variable-state changes during program execution.

## Planned modules

- `ast_engine/` - AST parsing and non-destructive capture-hook injection.
- `tracer/` - Runtime execution tracing.
- `storage/` - In-memory SQLite state storage and delta handling.
- `tui/` - Terminal user interface.
- `cli/` - Command-line entry point and integration work.

## Development environment

- Python 3.14 or newer
- Git and GitHub
- A local virtual environment named `venv`

## Current status

Day 1 project skeleton complete.
