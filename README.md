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
│
├── ast_engine/
├── storage/
├── tracer/
├── tui/
├── cli/
├── tests/
├── README.md
└── .gitignore