from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    
class Token(BaseModel):
    username: str
    display_name: str
    token_type: str
    access_token: str
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str



