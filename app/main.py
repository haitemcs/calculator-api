from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="Precision Calculator API",
    description="A simple API to perform basic arithmetic operations like addition, subtraction, multiplication, and division.",
    version="1.0.0"
)

app.include_router(router)