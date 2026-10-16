"""Helpers for password hashing and token-based authentication."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# Use a password-hashing algorithm with parameters recommended by pwdlib.
password_hash = PasswordHash.recommended()

# FastAPI extracts the token from the Authorization: Bearer <token> header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    """Hash a password before it is saved to the database."""
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Compare a login password with the stored hash."""
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    """Create a signed, short-lived JWT for one user."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # 'sub' identifies the user and 'exp' is checked when the token is decoded.
    # JWT payloads are signed, not encrypted, so do not put secrets in them.
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate a token and return its active account.

    Protected endpoints use Depends(get_current_user), so they don't repeat
    token parsing and user lookup on every route.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        # Give the client one generic message for malformed or expired tokens.
        raise unauthorized from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user
