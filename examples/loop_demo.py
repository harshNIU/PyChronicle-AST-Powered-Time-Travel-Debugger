"""Example with a loop, used to demo tracer max_steps truncation."""


def running_total(n):
    total = 0
    for i in range(n):
        total += i
    return total


result = running_total(50)
print("Result:", result)