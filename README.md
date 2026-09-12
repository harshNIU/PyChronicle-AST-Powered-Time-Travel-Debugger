# PyChronicle — AST-Powered Time-Travel Debugger

PyChronicle is a Python time-travel debugger that records program execution state so developers can inspect historical variable values without repeatedly restarting the program.

## Project Architecture

PyChronicle is organized into five modules:

- `ast_engine/` — AST parsing and source transformation.
- `tracer/` — Runtime execution tracing using `sys.settrace`.
- `storage/` — SQLite-based state storage.
- `tui/` — Terminal user interface.
- `cli/` — Command-line interface and integration.

## Project Structure

```text
PyChronicle-AST-Powered-Time-Travel-Debugger/
├── ast_engine/
├── tracer/
├── storage/
├── tui/
├── cli/
├── README.md
└── .gitignore
```