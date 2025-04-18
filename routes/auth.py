import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from schemas.auth_schemas import UserCreate, LoginRequest, Token

from database import get_db
from services.auth_service import (
    authenticate_user,
    create_user,
    create_user_token
)
from services.exceptions import (
    RegistrationError,
    AuthenticationError
)
from config import AUTH_ENDPOINTS_HTML

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/", response_class=HTMLResponse)
async def auth_root():
    return HTMLResponse(content=AUTH_ENDPOINTS_HTML)


@router.post("/register", 
             status_code=status.HTTP_201_CREATED, 
             response_model=Token)
async def register(
    request: Request,
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Registering user with email: {user_data.email}")
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        token = create_user_token(user)
        return token

    except RegistrationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an unexpected error"
        )


@router.post("/login", 
             response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest, 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Authenticating user with email: {login_data.email}")
        user = authenticate_user(db, login_data.email, login_data.password)
        token = create_user_token(user)
        return token

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )