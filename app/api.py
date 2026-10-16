from fastapi import APIRouter,Depends,HTTPException,Query,Response,status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Task,TaskStatus,User
from app.schemas import TaskCreate,TaskPage,TaskRead,TaskUpdate,Token,UserCreate,UserRead
from app.security import create_access_token,get_current_user,hash_password,verify_password
from app.tasks import process_task
router=APIRouter(prefix="/api/v1")
@router.post("/auth/register",response_model=UserRead,status_code=201)
def register(data:UserCreate,db:Session=Depends(get_db)):
    email=data.email.lower()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Account already exists")
    user=User(email=email,hashed_password=hash_password(data.password));db.add(user);db.commit();db.refresh(user);return user
@router.post("/auth/token",response_model=Token)
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==form.username.lower()))
    if not user or not verify_password(form.password,user.hashed_password) or not user.is_active:raise HTTPException(401,"Incorrect email or password",headers={"WWW-Authenticate":"Bearer"})
    return Token(access_token=create_access_token(user.id))
@router.get("/auth/me",response_model=UserRead)
def me(user:User=Depends(get_current_user)):return user
@router.post("/tasks",response_model=TaskRead,status_code=status.HTTP_202_ACCEPTED)
def create_task(data:TaskCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    task=Task(owner_id=user.id,name=data.name,operation=data.operation,input_data=data.input_data);db.add(task);db.commit();db.refresh(task)
    try:process_task.delay(task.id)
    except Exception:
        task.status=TaskStatus.FAILURE;task.error_message="Task could not be queued; check broker availability.";db.commit()
        raise HTTPException(503,"Background task broker unavailable")
    return task
@router.get("/tasks",response_model=TaskPage)
def list_tasks(status_filter:TaskStatus|None=Query(None,alias="status"),limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=select(Task).where(Task.owner_id==user.id);cq=select(func.count()).select_from(Task).where(Task.owner_id==user.id)
    if status_filter is not None:q=q.where(Task.status==status_filter);cq=cq.where(Task.status==status_filter)
    items=db.scalars(q.order_by(Task.created_at.desc()).limit(limit).offset(offset)).all()
    return TaskPage(items=items,total=db.scalar(cq) or 0,limit=limit,offset=offset)
def owned(task_id:str,db:Session,user:User)->Task:
    item=db.scalar(select(Task).where(Task.id==task_id,Task.owner_id==user.id))
    if item is None:raise HTTPException(404,"Task not found")
    return item
@router.get("/tasks/{task_id}",response_model=TaskRead)
def get_task(task_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):return owned(task_id,db,user)
@router.patch("/tasks/{task_id}",response_model=TaskRead)
def update_task(task_id:str,data:TaskUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=owned(task_id,db,user)
    if item.status in {TaskStatus.PENDING,TaskStatus.RUNNING}:raise HTTPException(409,"Cannot rename a task while it is running")
    if data.name is not None:item.name=data.name
    db.commit();db.refresh(item);return item
@router.delete("/tasks/{task_id}",status_code=204)
def delete_task(task_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    db.delete(owned(task_id,db,user));db.commit();return Response(status_code=204)
