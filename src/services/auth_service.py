import logging
from datetime import datetime, timedelta, UTC

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import DbUser
from src.utils.exceptions import (
    EmailNotFoundError, 
    PasswordIncorrectError,
    UsernameExistsError,
    EmailExistsError,
    WeakPasswordError,
    UsernameTooShortError,
    AuthenticationError
)
from src.utils.password import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    validate_password_strength,
    create_refresh_token,
    get_token_hash,
    verify_token
)
from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
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
        last_seen=datetime.now(UTC),
        hashed_refresh_token=None,
        refresh_token_expires_at=None
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

    logger.info(f"User credentials verified: {user.username}")
    return user


def create_and_store_tokens(db: Session, user: DbUser) -> Token:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_expire_time = datetime.now(UTC) + refresh_token_expires

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    hashed_refresh = get_token_hash(refresh_token)

    user.hashed_refresh_token = hashed_refresh
    user.refresh_token_expires_at = refresh_expire_time
    user.last_seen = datetime.now(UTC)

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Tokens created and refresh token stored for user: {user.username}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            username=user.username,
            display_name=user.display_name
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing refresh token for user {user.username}: {e}")
        raise AuthenticationError("Failed to finalize authentication session.")


def refresh_access_token(db: Session, provided_refresh_token: str) -> Token:
    try:
        payload = jwt.decode(provided_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Refresh token missing 'sub' claim.")
            raise AuthenticationError("Invalid refresh token.")
    except JWTError as e:
        logger.warning(f"Refresh token validation failed: {e}")
        raise AuthenticationError(f"Invalid refresh token: {e}")

    user = get_user_by_username(db, username)
    if user is None:
        logger.warning(f"User '{username}' from refresh token not found.")
        raise AuthenticationError("Invalid refresh token.")

    if not user.hashed_refresh_token or not user.refresh_token_expires_at:
        logger.warning(f"User '{username}' has no stored refresh token.")
        raise AuthenticationError("Refresh token not found or revoked.")

    if datetime.now(UTC) > user.refresh_token_expires_at:
        logger.warning(f"Refresh token expired for user '{username}'.")
        raise AuthenticationError("Refresh token expired.")

    if not verify_token(provided_refresh_token, user.hashed_refresh_token):
        logger.warning(f"Provided refresh token does not match stored hash for user '{username}'.")
        raise AuthenticationError("Invalid refresh token.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    user.last_seen = datetime.now(UTC)
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating last_seen during token refresh for {user.username}: {e}")

    logger.info(f"Access token refreshed for user: {user.username}")
    return Token(
        access_token=new_access_token,
        refresh_token=provided_refresh_token,
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
