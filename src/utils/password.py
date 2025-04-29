from datetime import datetime, timedelta, UTC
from typing import Dict, Any

from jose import jwt
from passlib.context import CryptContext
import bcrypt

from src.config import SECRET_KEY, ALGORITHM


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 1
REQUIRE_SPECIAL_CHARS = False
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_token_hash(token: str) -> str:
    return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_token(plain_token: str, hashed_token: str) -> bool:
    if not plain_token or not hashed_token:
        return False
    try:
        return bcrypt.checkpw(plain_token.encode('utf-8'), hashed_token.encode('utf-8'))
    except ValueError: # Handle potential error if hash format is wrong
        return False


def create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()

    expire = datetime.now(UTC) + expires_delta

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

    if REQUIRE_SPECIAL_CHARS and not any(char in SPECIAL_CHARS for char in password):
        return False, f"Password must contain at least one special character ({SPECIAL_CHARS})"

    return True, ""