class ChimeoError(Exception):
    """Base exception class for all Chimeo application errors."""
    default_message: str = "An error occurred"
    
    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class AuthenticationError(ChimeoError):
    """Base class for authentication-related errors."""
    default_message = "Authentication failed"

class EmailNotFoundError(AuthenticationError):
    default_message = "Email not found"

class PasswordIncorrectError(AuthenticationError):
    default_message = "Incorrect password"


class RegistrationError(ChimeoError):
    """Base class for registration-related errors."""
    default_message = "Registration failed"

class UsernameExistsError(RegistrationError):
    default_message = "Username already taken"

class EmailExistsError(RegistrationError):
    default_message = "Email already registered"

class WeakPasswordError(RegistrationError):
    default_message = "Password does not meet strength requirements"

class UsernameTooShortError(RegistrationError):
    default_message = "Username must be at least 3 characters long"
    pass
