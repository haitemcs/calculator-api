from datetime import datetime,timedelta,timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User
password_hash=PasswordHash.recommended()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
def hash_password(password:str)->str:return password_hash.hash(password)
def verify_password(password:str,hashed:str)->bool:return password_hash.verify(password,hashed)
def create_access_token(user_id:int)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub":str(user_id),"exp":exp},settings.secret_key,algorithm="HS256")
def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db))->User:
    error=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired credentials",headers={"WWW-Authenticate":"Bearer"})
    try: user_id=int(jwt.decode(token,settings.secret_key,algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError,KeyError,TypeError,ValueError): raise error
    user=db.get(User,user_id)
    if user is None or not user.is_active: raise error
    return user
