from fastapi import APIRouter

from app.schemas import Numbers
from app.services import calculator

router = APIRouter()


@router.post("/add")
def add(numbers: Numbers):
    result = calculator.add(numbers.a, numbers.b)
    return {
        "result": result
    }


@router.post("/subtract")
def subtract(numbers: Numbers):
    result = calculator.subtract(numbers.a, numbers.b)
    return {
        "result": result
    }


@router.post("/multiply")
def multiply(numbers: Numbers):
    result = calculator.multiply(numbers.a, numbers.b)
    return {
        "result": result
    }


@router.post("/divide")
def divide(numbers: Numbers):
    result = calculator.divide(numbers.a, numbers.b)
    return {
        "result": result
    }