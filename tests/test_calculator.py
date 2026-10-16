"""Small unit tests for the calculator logic.

These tests don't need PostgreSQL or Redis because calculate() is a normal
Python function. That makes it quick to check the accepted operations and errors.
"""
import pytest

from app.tasks import calculate


def test_addition() -> None:
    assert calculate({"operation": "add", "a": 2, "b": 3})["result"] == 5


def test_division() -> None:
    assert calculate({"operation": "divide", "a": 10, "b": 2})["result"] == 5


def test_sum() -> None:
    assert calculate({"operation": "sum", "numbers": [1, 2, 3]})["result"] == 6


def test_division_by_zero_is_rejected() -> None:
    # pytest.raises passes only when the expected exception is raised.
    with pytest.raises(ValueError, match="zero"):
        calculate({"operation": "divide", "a": 1, "b": 0})


def test_unknown_operation_is_rejected() -> None:
    # The calculator accepts named operations, not arbitrary Python expressions.
    with pytest.raises(ValueError, match="Unsupported"):
        calculate(
            {
                "operation": "eval",
                "expression": "__import__('os').system('id')",
            }
        )
