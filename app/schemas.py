from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import TaskStatus
class UserCreate(BaseModel):
    email: EmailStr
    password: str=Field(min_length=8,max_length=128)
class UserRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; email:EmailStr; is_active:bool; created_at:datetime
class Token(BaseModel):
    access_token:str
    token_type:str="bearer"
class TaskCreate(BaseModel):
    name:str=Field(default="Background task",min_length=1,max_length=160)
    operation:str=Field(default="calculate",min_length=1,max_length=40)
    input_data:dict
class TaskUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=1,max_length=160)
class TaskRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; name:str; operation:str; input_data:dict; result_data:dict|None
    status:TaskStatus; error_message:str|None; retry_count:int
    created_at:datetime; updated_at:datetime; started_at:datetime|None; finished_at:datetime|None
class TaskPage(BaseModel):
    items:list[TaskRead]; total:int; limit:int; offset:int
