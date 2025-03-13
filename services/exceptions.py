
# services/exceptions.py
class EmailNotFoundError(Exception):
    """Raised when the username does not exist in the database."""
    pass


class PasswordIncorrectError(Exception):
    """Raised when the password is incorrect."""
    pass
