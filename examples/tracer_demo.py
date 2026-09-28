"""Small example program for trying out the PyChronicle tracer."""


def running_total(numbers):
    total = 0
    for n in numbers:
        total += n
    return total


result = running_total([1, 2, 3])
print("Result:", result)