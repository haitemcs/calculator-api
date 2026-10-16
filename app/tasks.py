from datetime import datetime,timezone
from celery import Celery
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import Task,TaskStatus
celery_app=Celery("async_task_platform",broker=settings.celery_broker_url,backend=settings.celery_result_backend)
celery_app.conf.update(task_serializer="json",accept_content=["json"],result_serializer="json",timezone="UTC",enable_utc=True,task_acks_late=True,worker_prefetch_multiplier=1,task_reject_on_worker_lost=True,task_track_started=True)
def calculate(data:dict)->dict:
    op=data.get("operation")
    if op=="sum":
        values=data.get("numbers")
        if not isinstance(values,list) or not values or not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in values): raise ValueError("numbers must be a non-empty list of numbers")
        return {"operation":op,"result":sum(values)}
    a,b=data.get("a"),data.get("b")
    if op not in {"add","subtract","multiply","divide"}: raise ValueError("Unsupported operation")
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in (a,b)): raise ValueError("a and b must be numbers")
    if op=="add": result=a+b
    elif op=="subtract": result=a-b
    elif op=="multiply": result=a*b
    else:
        if b==0: raise ValueError("division by zero")
        result=a/b
    return {"operation":op,"a":a,"b":b,"result":result}
@celery_app.task(bind=True,name="app.tasks.process_task",autoretry_for=(ConnectionError,),retry_backoff=True,retry_jitter=True,max_retries=3)
def process_task(self,task_id:str)->dict:
    db:Session=SessionLocal()
    try:
        task=db.get(Task,task_id)
        if task is None:return {"status":"missing","task_id":task_id}
        task.status=TaskStatus.RUNNING;task.started_at=datetime.now(timezone.utc);task.retry_count=self.request.retries;task.error_message=None;db.commit()
        try:
            if task.operation!="calculate":raise ValueError("Unsupported task type")
            result=calculate(task.input_data)
        except (ValueError,TypeError) as exc:
            task.status=TaskStatus.FAILURE;task.error_message=str(exc)[:2000];task.finished_at=datetime.now(timezone.utc);db.commit()
            return {"task_id":task_id,"status":"failure"}
        task.result_data=result;task.status=TaskStatus.SUCCESS;task.finished_at=datetime.now(timezone.utc);db.commit()
        return {"task_id":task_id,"status":"success","result":result}
    except Exception:db.rollback();raise
    finally:db.close()
