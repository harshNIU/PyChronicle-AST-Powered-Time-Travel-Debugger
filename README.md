<<<<<<< HEAD
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
=======
# PyChronicle

**PyChronicle** is an experimental time-travel debugger for Python.

The goal of PyChronicle is to allow developers to inspect the execution history of a Python program and move backward and forward through previous program states without having to restart and rerun the program.

## The Problem

When debugging a program normally, developers usually execute the program, reach a breakpoint, inspect the current state, and then continue execution.

If something important happened earlier, they often have to restart the program and reproduce the same execution path.

This can make debugging difficult, especially when the bug depends on a previous change in program state.

PyChronicle aims to solve this by recording execution history while the program runs.

## Core Idea

PyChronicle will observe a Python program during execution and record relevant changes in its state.

The planned pipeline is:

```text
Python Program
      │
      ▼
AST Processing
      │
      ▼
Instrumented Program
      │
      ▼
Execution Engine
   sys.settrace
      │
      ▼
State Changes
      │
      ▼
State Storage
      │
      ▼
Timeline
      │
      ▼
CLI / UI
      │
      ▼
Backward / Forward Navigation
```

## Main Components

### 1. AST Rewriter

Uses Python's `ast` module to inspect and potentially transform Python source code.

The AST layer will help PyChronicle understand the structure of the program and prepare it for tracking.

### 2. Execution Engine

Uses Python's tracing capabilities, primarily `sys.settrace`, to observe program execution.

It will eventually be responsible for detecting relevant execution events and passing state information to the storage layer.

### 3. State Storage

Stores information about program execution and state changes.

The project will use MySQL for persistent storage.

The initial focus will be on designing a useful representation of state changes rather than trying to store the entire program state after every line.

### 4. Timeline

Represents the chronological history of program execution.

The timeline will eventually allow the user to move between previous execution states.

### 5. CLI / UI

Provides an interface for interacting with the recorded execution history.

The initial version will focus on making the underlying functionality work before building a more advanced interface.

## Current Status

### Day 1

* Repository structure created
* Initial architecture documented
* Development roadmap created
* Basic Python tracing prototype started
* Example program added
* Testing structure created

The project is currently in the foundation/prototyping stage.

## Planned Development

The project will be developed incrementally:

1. Python fundamentals
2. Object-oriented Python
3. MySQL
4. Database schema
5. Python-MySQL integration
6. `sys.settrace` fundamentals
7. Line-level execution tracking
8. Variable/state tracking
9. State representation
10. Timeline navigation
11. CLI
12. AST processing/instrumentation
13. Testing and integration
14. Final UI

## Project Status

**Stage:** Prototype / Foundation

PyChronicle is currently an educational and experimental project being developed incrementally by a student team.
>>>>>>> origin/main