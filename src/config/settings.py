import os
import secrets
from typing import Final, List
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: Final[str] = os.getenv("DATABASE_URL", "sqlite:///./chimeo.db")

DEFAULT_SECRET_KEY = secrets.token_hex(32)
SECRET_KEY: Final[str] = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
ALGORITHM: Final[str] = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Default 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")) # Default 7 days

HOST: Final[str] = os.getenv("HOST", "0.0.0.0")
PORT: Final[int] = int(os.getenv("PORT", "8000"))

CORS_ENABLED: Final[bool] = os.getenv("CORS_ENABLED", "true").lower() == "true"
CORS_ORIGINS: Final[List[str]] = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_METHODS: Final[List[str]] = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE").split(",")
CORS_HEADERS: Final[List[str]] = os.getenv("CORS_HEADERS", "Authorization,Content-Type").split(",")

WS_HEARTBEAT_INTERVAL: Final[int] = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))  # seconds

DEBUG: Final[bool] = os.getenv("DEBUG", "false").lower() == "true"

if SECRET_KEY == DEFAULT_SECRET_KEY and not DEBUG:
    print("WARNING: Using auto-generated SECRET_KEY in production. Set a proper SECRET_KEY in environment variables.") 