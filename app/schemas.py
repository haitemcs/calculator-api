from pydantic import BaseModel


class Numbers(BaseModel):
    a: float
    b: float

class Result (BaseModel):
    result: float

