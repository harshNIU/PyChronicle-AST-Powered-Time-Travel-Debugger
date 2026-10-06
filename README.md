# PyChronicle - AST-Powered Time-Travel Debugger

PyChronicle is an experimental Python time-travel debugger. It is designed to record program execution and help developers inspect previous program states without restarting the program.

## Problem Statement

Traditional debuggers mainly allow developers to move forward through a program. When an error occurs, developers may need to restart the program several times to understand what happened.

PyChronicle aims to solve this problem by allowing developers to move backward and inspect earlier execution states.

## Features

- Python source-code analysis using the Abstract Syntax Tree (AST)
- Recording of program execution
- Inspection of previous program states
- Storage of execution information
- Command-line debugging support
- Interactive debugging interface

## Project Structure

```text
PyChronicle/
├── ast_engine/
├── storage/
├── tracer/
├── tui/
├── cli/
├── tests/
├── README.md
└── .gitignore


## Looking up a single variable's history

The core "time travel" question: what was this variable at each point
during the run?


python3 tracer/query_timeline.py --db timeline.db --variable total

Prints every step where that variable changed, in order, with the
function, line number and source text.

## Comparing two runs

Trace the same program twice (e.g. before and after a change) into two
separate databases, then compare them:


python3 tracer/run_tracer.py your_script.py --db before.db --quiet
python3 tracer/run_tracer.py your_script.py --db after.db --quiet
python3 tracer/compare_timelines.py --old before.db --new after.db

Reports function call count changes, new exceptions introduced in the
second run, and exceptions that were present before but are now gone.