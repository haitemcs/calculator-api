from unittest import result

from fastapi import APIRouter, HTTPException
from app.schemas import Numbers , Result
from app.services import calculator
from app.logging import logger


router = APIRouter()


#Every successful response from this endpoint must match the Result model.
@router.post("/add", response_model=Result)
def add(numbers: Numbers):
    result = calculator.add(numbers.a, numbers.b)
    return {
        "result": result
    }

@router.post("/subtract", response_model=Result)
def subtract(numbers: Numbers):
    result = calculator.subtract(numbers.a, numbers.b)
    return {
        "result": result
    }

@router.post("/multiply", response_model=Result)
def multiply(numbers: Numbers):
    result = calculator.multiply(numbers.a, numbers.b)
    return {
        "result": result
    }

@router.post("/divide", response_model=Result)
def divide(numbers: Numbers):
    if numbers.b == 0:
        raise HTTPException(
            status_code=400,
            detail="Division by zero is not allowed."
        )

    result = calculator.divide(numbers.a, numbers.b)

    return {
        "result": result
    }

@router.post("/average", response_model=Result)

def average (numbers: Numbers):
    result = calculator.add(numbers.a, numbers.b)/2
    return {
        "result": result
    }