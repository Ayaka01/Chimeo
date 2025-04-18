from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, Any

from jose import jwt
from passlib.context import CryptContext

from src.config import SECRET_KEY, ALGORITHM


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 1
REQUIRE_SPECIAL_CHARS = False
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

    if REQUIRE_SPECIAL_CHARS and not any(char in SPECIAL_CHARS for char in password):
        return False, f"Password must contain at least one special character ({SPECIAL_CHARS})"

    return True, ""