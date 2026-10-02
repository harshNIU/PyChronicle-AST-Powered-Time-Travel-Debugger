
## Exporting a timeline to JSON

For tools outside this module (the team's CLI/TUI, a notebook, anything
that isn't Python at all) a saved timeline can be exported to plain JSON
instead of being read from SQLite directly:

```
python3 tracer/export_timeline.py --db timeline.db --pretty
python3 tracer/export_timeline.py --db timeline.db --function add_numbers --out add_numbers.json
```

Each exported step has `step_index`, `event_type`, `function_name`,
`depth`, `line_number`, `changed_vars` (a real JSON object, not a string),
`return_value`, `exception_type`, `exception_message`, and `source_text`.