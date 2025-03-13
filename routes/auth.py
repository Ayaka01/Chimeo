# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas.auth_schemas import UserCreate, LoginRequest

from database import get_db
from services.auth_service import (
    authenticate_user,
    create_user,
    create_user_token,
    get_user_by_email,
    get_user_by_username
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    try:
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )

        token = create_user_token(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return token


@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint"""

    try:
        # Authenticate user
        user = authenticate_user(db, login_data.email, login_data.password)
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create and return token
    token = create_user_token(user)
    return token


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login endpoint"""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_user_token(user)

    # ¿No puedo simplemente devolver el token? O sea, ¿por qué necesito un diccionario?
    return {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "user_id": token.user_id,
        "username": token.username,
        "display_name": token.display_name
    }
