import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.user import User
from utils.password import verify_password, get_password_hash, create_access_token
from config import SECRET_KEY, ALGORITHM

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    display_name: str

# OAuth2 scheme for JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user_by_email(db: Session, email: str):
    """Get user by email from database"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str, display_name: str):
    """Create a new user"""
    # Generate a unique ID
    user_id = str(uuid.uuid4())
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create the user object
    db_user = User(
        id=user_id,
        email=email,
        hashed_password=hashed_password,
        display_name=display_name,
        last_seen=datetime.utcnow()
    )
    
    # Add and commit to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by email and password"""
    user = get_user_by_email(db, email)
    
    if not user:
        return False
        
    if not verify_password(password, user.hashed_password):
        return False
        
    # Update last seen
    user.last_seen = datetime.utcnow()
    db.commit()
    
    return user

def create_user_token(user: User):
    """Create JWT token for authenticated user"""
    access_token_expires = timedelta(minutes=60 * 24)  # 1 day
    
    # Create token with user ID in the payload
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        display_name=user.display_name
    )

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
        
    # Update last seen
    user.last_seen = datetime.utcnow()
    db.commit()
    
    return user