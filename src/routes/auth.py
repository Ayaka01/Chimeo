import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.schemas.auth_schemas import UserCreate, LoginRequest, Token
from pydantic import BaseModel # For refresh token request body

from src.database import get_db
from src.services.auth_service import (
    authenticate_user,
    create_user,
    create_and_store_tokens,
    refresh_access_token
)

from src.config import AUTH_ENDPOINTS_HTML
from src.utils.exceptions import RegistrationError, AuthenticationError, APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/", response_class=HTMLResponse)
async def auth_root():
    return HTMLResponse(content=AUTH_ENDPOINTS_HTML)


@router.post("/register", 
             response_model=Token,
             status_code=status.HTTP_201_CREATED,
             responses= {
                 status.HTTP_400_BAD_REQUEST: {"description": "Username/Email already exists or validation failed"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
             }
             )
async def register(
    _: Request,
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Registering user with email: {user_data.email}")
        user = create_user(
            db=db,
            username=user_data.username,
            email=str(user_data.email),
            password=user_data.password,
            display_name=user_data.display_name
        )
        token_response = create_and_store_tokens(db=db, user=user)
        return token_response

    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}", exc_info=True)
        if isinstance(e, APIError):
             raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an unexpected internal error"
        )


@router.post("/login", 
             response_model=Token,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error or failed to store token"}
             })
async def login(
    _: Request,
    login_data: LoginRequest, 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Authenticating user with email: {login_data.email}")
        user = authenticate_user(db, str(login_data.email), login_data.password)
        token_response = create_and_store_tokens(db=db, user=user)
        return token_response

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to an unexpected error",
            headers={"WWW-Authenticate": "Bearer"},
        )

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", 
             response_model=Token,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired refresh token"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
             })
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info("Attempting to refresh access token.")
        new_token_response = refresh_access_token(db=db, provided_refresh_token=refresh_request.refresh_token)
        return new_token_response
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to an unexpected error"
        )