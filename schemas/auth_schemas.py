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
    access_token: str
    token_type: str
    username: str
    display_name: str
