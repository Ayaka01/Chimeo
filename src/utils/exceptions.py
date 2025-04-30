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

# --- Friendship/User Related Errors --- 

class FriendshipError(APIError):
    """Base class for friendship/request related errors."""
    def __init__(self, status_code: int = 400, detail: str = "Friendship operation failed", error_code: str = "FRIENDSHIP_ERROR"):
        super().__init__(status_code=status_code, detail=detail, error_code=error_code)

class UserNotFoundError(FriendshipError):
     def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=404, detail=detail, error_code="USER_NOT_FOUND")

class FriendRequestNotFoundError(FriendshipError):
    def __init__(self, detail: str = "Friend request not found"):
        super().__init__(status_code=404, detail=detail, error_code="FRIEND_REQUEST_NOT_FOUND")

class FriendshipExistsError(FriendshipError):
    def __init__(self, detail: str = "Users are already friends"):
        super().__init__(status_code=409, detail=detail, error_code="FRIENDSHIP_ALREADY_EXISTS")

class FriendRequestExistsError(FriendshipError):
     def __init__(self, detail: str = "Friend request already exists"):
        super().__init__(status_code=409, detail=detail, error_code="FRIEND_REQUEST_ALREADY_EXISTS")

class InvalidFriendRequestStateError(FriendshipError):
     def __init__(self, detail: str = "Friend request is not in a valid state for this action"):
        super().__init__(status_code=400, detail=detail, error_code="INVALID_FRIEND_REQUEST_STATE")

class CannotFriendSelfError(FriendshipError):
     def __init__(self, detail: str = "Cannot send friend request to yourself"):
        super().__init__(status_code=400, detail=detail, error_code="CANNOT_FRIEND_SELF")

class NotAuthorizedError(APIError):
     # Inherits directly from APIError as it might apply outside friendships
     def __init__(self, detail: str = "Operation not authorized"):
        super().__init__(status_code=403, detail=detail, error_code="NOT_AUTHORIZED")

# --- Message Related Errors --- 

class MessageNotFoundError(APIError):
    def __init__(self, detail: str = "Message not found"):
        super().__init__(status_code=404, detail=detail, error_code="MESSAGE_NOT_FOUND")

# (Add more message errors if needed)
