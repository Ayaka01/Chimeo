# services/auth_service.py
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from services.exceptions import EmailNotFoundError, PasswordIncorrectError
from utils.password import verify_password, get_password_hash, create_access_token
from config import SECRET_KEY, ALGORITHM
from schemas.auth_schemas import Token

# OAuth2 scheme for JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, email: str, password: str, display_name: str):
    existing_username = get_user_by_username(db, username)
    if existing_username:
        print("EXISTING USERNAME")
        raise ValueError("Username already taken")

    existing_email = get_user_by_email(db, email)
    if existing_email:
        print("EXISTING EMAIL")
        raise ValueError("Email already registered")

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create the user object
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        display_name=display_name,
        last_seen=datetime.utcnow()
    )

    # Add and commit to database
    print("ANTES ADD")
    db.add(db_user)
    print("DESPUES ADD")
    db.commit()
    db.refresh(db_user)
    print("ANTES RETURN")
    print(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user:
        raise EmailNotFoundError(f"Email '{email}' not found")

    if not verify_password(password, user.hashed_password):
        raise PasswordIncorrectError("Incorrect password")

    # Update last seen
    user.last_seen = datetime.utcnow()
    db.commit()

    return user


def create_user_token(user: User):
    """Create JWT token for authenticated user"""
    access_token_expires = timedelta(minutes=60 * 24)  # 1 day
    print("ANTES CREAR TOKEN")
    # Create token with user ID in the payload
    access_token_created = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    print("ANTES DE RETURN, DESPUES CREAR TOKEN")
    return Token(
        access_token=access_token_created,
        token_type="bearer",
        username=user.username,
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
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    # Update last seen
    user.last_seen = datetime.utcnow()
    db.commit()

    return user
