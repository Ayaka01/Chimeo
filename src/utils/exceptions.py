from typing import Dict, Any, Optional, List

class APIError(Exception):
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_code: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.errors = errors or []
        super().__init__(detail)


class AuthenticationError(APIError):
    """Base class for authentication failures."""
    def __init__(
        self, 
        status_code: int = 401,
        detail: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR"
    ):
        super().__init__(status_code=status_code, detail=detail, error_code=error_code)

class EmailNotFoundError(AuthenticationError):
    def __init__(self, detail: str = "Email not found"):
        super().__init__(status_code=404, detail=detail, error_code="EMAIL_NOT_FOUND")

class PasswordIncorrectError(AuthenticationError):
    def __init__(self, detail: str = "Incorrect password"):
        super().__init__(status_code=401, detail=detail, error_code="INVALID_CREDENTIALS")

class RegistrationError(APIError):
    def __init__(
        self, 
        status_code: int = 400,
        detail: str = "Registration failed",
        error_code: str = "REGISTRATION_ERROR"
    ):
        super().__init__(status_code=status_code, detail=detail, error_code=error_code)

class UsernameExistsError(RegistrationError):
    def __init__(self, detail: str = "Username already taken"):
        super().__init__(status_code=409, detail=detail, error_code="USERNAME_EXISTS")

class EmailExistsError(RegistrationError):
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(status_code=409, detail=detail, error_code="EMAIL_EXISTS")

class WeakPasswordError(RegistrationError):
    def __init__(self, detail: str = "Password does not meet strength requirements"):
        super().__init__(status_code=400, detail=detail, error_code="WEAK_PASSWORD")

class UsernameTooShortError(RegistrationError):
    def __init__(self, detail: str = "Username must be at least 3 characters long"):
        super().__init__(status_code=400, detail=detail, error_code="USERNAME_TOO_SHORT")
