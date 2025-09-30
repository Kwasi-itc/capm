"""A simple command-line calculator supporting add, subtract, multiply and divide.

Usage examples (Windows cmd):
    python examples\app.py add 1 2
    python examples\app.py sub 5 3
    python examples\app.py mul 4 7
    python examples\app.py div 10 2
"""
import argparse
import operator
import sys
from typing import Callable, Dict

# Mapping of operation names to the corresponding arithmetic functions
OPERATIONS: Dict[str, Callable[[float, float], float]] = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": operator.truediv,
}


def calculate(op_name: str, a: float, b: float) -> float:
    """Perform the requested arithmetic operation on two operands."""
    if op_name not in OPERATIONS:
        raise ValueError(f"Unsupported operation '{op_name}'.")
    if op_name == "div" and b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    return OPERATIONS[op_name](a, b)


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Simple command-line calculator")
    parser.add_argument(
        "operation",
        choices=OPERATIONS.keys(),
        help="Arithmetic operation: add, sub, mul, div",
    )
    parser.add_argument("a", type=float, help="First operand")
    parser.add_argument("b", type=float, help="Second operand")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    try:
        result = calculate(args.operation, args.a, args.b)
        print(result)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
