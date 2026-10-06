class Counter:
    def __init__(self, value):
        self.value = value

    def increment(self):
        self.value += 1
        return self.value

counter = Counter(0)
result = counter.increment()
print(result)
