import logging
from datetime import datetime, timedelta, UTC

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import DbUser
from src.services.exceptions import (
    EmailNotFoundError, 
    PasswordIncorrectError,
    UsernameExistsError,
    EmailExistsError,
    WeakPasswordError,
    UsernameTooShortError
)
from src.utils.password import verify_password, get_password_hash, create_access_token, validate_password_strength
from src.config import SECRET_KEY, ALGORITHM
from src.schemas.auth_schemas import Token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_user_by_email(db: Session, email: str) -> DbUser | None:
    return db.query(DbUser).filter(DbUser.email == email).first()


def get_user_by_username(db: Session, username: str) -> DbUser | None:
    return db.query(DbUser).filter(DbUser.username == username).first()


def create_user(db: Session, username: str, email: str, password: str, display_name: str) -> DbUser:
    if len(username) < 3:
        logger.warning(f"Attempt to register with username shorter than 3 characters: '{username}'")
        raise UsernameTooShortError("Username must be at least 3 characters long")

    existing_username = get_user_by_username(db, username)
    if existing_username:
        logger.warning(f"Username '{username}' already taken")
        raise UsernameExistsError("Username already taken")

    existing_email = get_user_by_email(db, email)
    if existing_email:
        logger.warning(f"Email '{email}' already registered")
        raise EmailExistsError("Email already registered")
    
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        logger.warning(f"Weak password attempted for user: {username}")
        raise WeakPasswordError(error_message)

    hashed_password = get_password_hash(password)

    db_user = DbUser(
        username=username,
        email=email,
        hashed_password=hashed_password,
        display_name=display_name,
        last_seen=datetime.now(UTC)
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {username}")
        return db_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise


def authenticate_user(db: Session, email: str, password: str) -> DbUser:
    user = get_user_by_email(db, email)

    if not user:
        logger.warning(f"Authentication failed: Email '{email}' not found")
        raise EmailNotFoundError(f"Email '{email}' not found")

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: Incorrect password for '{email}'")
        raise PasswordIncorrectError("Incorrect password")

    try:
        user.last_seen = datetime.now(UTC)
        db.commit()
        logger.info(f"User authenticated: {user.username}")
        return user

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating last_seen for user {user.username}: {e}")
        return user


def create_user_token(user: DbUser) -> Token:
    access_token_expires = timedelta(days=365 * 100)

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Token created for user: {user.username}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        display_name=user.display_name
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> DbUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")


    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception

    user = get_user_by_username(db, username)

    if user is None:
        logger.warning(f"Token validation failed: user '{username}' not found")
        raise credentials_exception

    try:
        user.last_seen = datetime.now(UTC)
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating last_seen for user {user.username}: {e}")

    return user
