import io
import sys
import pytest
import runpy
import os

# путь до файла
MODULE_PATH = "/Users/aleksandr/Downloads/Term_programming/LR_2/TaskOne/gen_fib.py"

def load_module():
    """Запускаем модуль и возвращаем его namespace"""
    ns = runpy.run_path(MODULE_PATH, run_name="__main__")
    return ns


def test_fib_elem_gen_sequence():
    ns = load_module()
    fib_elem_gen = ns["fib_elem_gen"]

    g = fib_elem_gen()
    seq = [next(g) for _ in range(10)]
    assert seq == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_my_genn_returns_zero_elements():
    ns = load_module()
    my_genn = ns["my_genn"]

    gen = my_genn()
    result = gen.send(0)
    assert result == ["0:"]


def test_my_genn_returns_one_element():
    ns = load_module()
    my_genn = ns["my_genn"]

    gen = my_genn()
    result = gen.send(1)
    assert result == ["1:", 0]


def test_my_genn_returns_five_elements():
    ns = load_module()
    my_genn = ns["my_genn"]

    gen = my_genn()
    result = gen.send(5)
    # 5 элементов: 0,1,1,2,3
    assert result == ["5:", 0, 1, 1, 2, 3]


def test_my_genn_negative_number():
    ns = load_module()
    my_genn = ns["my_genn"]

    gen = my_genn()
    result = gen.send(-3)
    assert result[0] == "-3:"
    assert "отрицательным" in result[1]


def test_my_genn_non_integer_input():
    ns = load_module()
    my_genn = ns["my_genn"]

    gen = my_genn()
    result = gen.send("abc")
    assert result[0] == "abc:"
    assert "целое число" in result[1]


def test_fib_coroutine_primes_generator():
    ns = load_module()
    my_genn = ns["my_genn"]

    # если fib_coroutine не prime-ит, будет StopIteration при первом send
    gen = my_genn()
    result = gen.send(2)
    assert result == ["2:", 0, 1]
