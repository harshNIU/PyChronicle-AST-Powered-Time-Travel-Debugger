"""A deliberately small target for `pychronicle run examples/loop_bug.py --tui`."""

total = 0
values = [2, 4, 6, 8]
for index, value in enumerate(values):
    total += value
    if index == 2:
        total *= 10  # Inspect the timeline to see the unexpected mutation.
print(total)
