#!/usr/bin/env python3
"""
A simple command-line calculator supporting addition, multiplication,
and division.

Usage examples:

    python -m examples.calculator add 1 2
    python -m examples.calculator multiply 3 4
    python -m examples.calculator divide 10 2
"""
from __future__ import annotations

import argparse


def add(a: float, b: float) -> float:
    """Return the sum of *a* and *b*."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Return the product of *a* and *b*."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return *a* divided by *b*.

    Raises
    ------
    ValueError
        If *b* is zero.
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b


def build_parser() -> argparse.ArgumentParser:
    """Create and return the top-level ``argparse`` parser."""
    parser = argparse.ArgumentParser(description="Simple command-line calculator")
    sub = parser.add_subparsers(dest="operation", required=True)

    # add
    p_add = sub.add_parser("add", help="Add two numbers")
    p_add.add_argument("a", type=float, help="First number")
    p_add.add_argument("b", type=float, help="Second number")

    # multiply
    p_mul = sub.add_parser("multiply", help="Multiply two numbers")
    p_mul.add_argument("a", type=float, help="First number")
    p_mul.add_argument("b", type=float, help="Second number")

    # divide
    p_div = sub.add_parser("divide", help="Divide two numbers")
    p_div.add_argument("a", type=float, help="Dividend")
    p_div.add_argument("b", type=float, help="Divisor")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.operation == "add":
        result = add(args.a, args.b)
    elif args.operation == "multiply":
        result = multiply(args.a, args.b)
    elif args.operation == "divide":
        result = divide(args.a, args.b)
    else:  # pragma: no cover
        raise RuntimeError("Unreachable operation requested")

    print(result)


if __name__ == "__main__":
    main()
