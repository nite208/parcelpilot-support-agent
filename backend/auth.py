import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_SECRET, JWT_ALGORITHM, MOCK_USERS

security = HTTPBearer()


def create_token(username):
    user = MOCK_USERS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {
        "sub": username,
        "role": user["role"],
        "account_id": user["account_id"],
        "account_name": user["account_name"],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    return decode_token(credentials.credentials)


def require_internal(credentials: HTTPAuthorizationCredentials = Security(security)):
    user = decode_token(credentials.credentials)
    if user.get("role") != "internal":
        raise HTTPException(status_code=403, detail="Internal access only")
    return user


def require_customer(credentials: HTTPAuthorizationCredentials = Security(security)):
    user = decode_token(credentials.credentials)
    if user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer access only")
    return user


def login(username, password):
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "account_id": user["account_id"],
        "account_name": user["account_name"]
    }