class FibonacchiLst:
    def __init__(self, instance):
        self.instance = instance   # сохраняем исходный список
        self.idx = 0               # текущий индекс при обходе
        # заранее построим множество чисел Фибоначчи до max(instance),
        # чтобы проверка принадлежности была быстрой (O(1))
        max_val = max(instance) if instance else 0
        self.fib_set = self._fib_up_to(max_val)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                res = self.instance[self.idx]
            except IndexError:
                raise StopIteration

            self.idx += 1

            if res in self.fib_set:
                return res

    @staticmethod
    def _fib_up_to(n):
        """Вернуть множество чисел Фибоначчи до n включительно"""
        fibs = {0, 1}
        a, b = 0, 1
        while b <= n:
            a, b = b, a + b
            fibs.add(a)
        return fibs


# пример
lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
print(list(FibonacchiLst(lst)))
