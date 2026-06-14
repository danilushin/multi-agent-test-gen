"""A tiny module to point the generator at:

    python -m mate examples/sample_module.py
"""


def add(a, b):
    return a + b


def is_even(n):
    return n % 2 == 0


def slugify(text):
    return "-".join(text.lower().split())
