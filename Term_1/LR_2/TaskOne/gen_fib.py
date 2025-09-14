import functools
from typing import Generator, List, Any

def fib_elem_gen() -> Generator[int, None, None]:
    """Генератор, возвращающий элементы ряда Фибоначчи"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def my_genn() -> Generator[Any, int, List[Any]]:
    """Сопрограмма для генерации ряда Фибоначчи"""
    while True:
        number_of_fib_elem = yield

        if not isinstance(number_of_fib_elem, int):
            l = [f"{number_of_fib_elem}:", "Ошибка: ожидается целое число (int)"]
            yield l
            continue

        if number_of_fib_elem < 0:
            l = [f"{number_of_fib_elem}:", "Ошибка: количество не может быть отрицательным"]
            yield l
            continue

        print(f"Генерируем {number_of_fib_elem} элементов ряда Фибоначчи")

        header = f"{number_of_fib_elem}:"
        # для n == 0 вернём только заголовок (без чисел)
        if number_of_fib_elem == 0:
            l = [header]
            yield l
            continue

        l = [header]
        a, b = 0, 1
        for _ in range(number_of_fib_elem):
            l.append(a)
            a, b = b, a + b

        # вернём готовый список
        yield l


def fib_coroutine(g):
    """Сопрограмма для генерации ряда Фибоначчи"""
    @functools.wraps(g)
    def inner(*args, **kwargs):
        gen = g(*args, **kwargs)
        next(gen)
        return gen
    return inner


my_genn = fib_coroutine(my_genn)

if __name__ == "__main__":

    gen = my_genn()
    result = gen.send(5)
    print("Получили: ",result)