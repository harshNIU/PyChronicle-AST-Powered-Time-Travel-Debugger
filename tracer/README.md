
## Step limits for long or infinite loops

```python
tracer = ExecutionTracer(target_file=__file__, max_steps=5000)
```

Once 5000 steps are captured, recording stops automatically. The traced
program keeps running as normal; only the recording is cut off, so a
long or infinite loop can't hang the tracer or fill memory. Check
`tracer.truncated` (True/False) to see if this happened. Same option
from the command line:

```
python3 tracer/run_tracer.py examples/loop_demo.py --max-steps 30 --summary
```

## Summary reports

```python
tracer.print_summary()
```

Prints total steps recorded, how many times each function was called,
and any exceptions raised. Also available from the command line with
`--summary` on `run_tracer.py`.

## Querying a saved timeline

Once a timeline has been saved to a database, it can be filtered without
rerunning the script:

```
python3 tracer/query_timeline.py --db timeline.db --function add_numbers
python3 tracer/query_timeline.py --db timeline.db --exceptions
python3 tracer/query_timeline.py --db timeline.db --summary
```