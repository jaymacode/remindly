from app.config import settings
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Header, HTTPException
from sqlalchemy.orm import Session
from app.models import User
from app.database import SessionLocal

SECRET_KEY = settings.secret_key  
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

def hash_password(password: str):
    password = password[:72].encode()
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode()

def verify_password(plain_password, hashed_password):
    plain_password = plain_password[:72].encode()
    return bcrypt.checkpw(plain_password, hashed_password.encode())

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def get_current_user(Authorization: str = Header(...)):
    # Only the header is a FastAPI parameter; an extra argument here would be read as a request-body field.
    return _authenticate(Authorization)


def _authenticate(Authorization: str, required_roles: Optional[list] = None):
    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = Authorization.split(" ")[1]
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.is_active != 1:
            raise HTTPException(status_code=403, detail="User inactive or not found")
        if required_roles and user.role not in required_roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        return user
    finally:
        db.close()

def require_roles(*roles: str):
    """Return a FastAPI dependency that authenticates the request and checks its role.

    Usage: current_user: User = Depends(require_roles("admin"))
    """
    allowed_roles = list(roles)

    def dependency(Authorization: str = Header(...)) -> User:
        return _authenticate(Authorization, required_roles=allowed_roles)

    return dependency
