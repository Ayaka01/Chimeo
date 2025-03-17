
# services/exceptions.py
class EmailNotFoundError(Exception):
    """Raised when the username does not exist in the database."""
    pass


class PasswordIncorrectError(Exception):
    """Raised when the password is incorrect."""
    pass


class BadRequestError(Exception):
    pass


class UserNotFoundError(BadRequestError):
    """Raised when the user does not exist in the database."""
    pass


class RequestToYourselfError(BadRequestError):
    """Raised when the user tries to send a friend request to themselves."""
    pass


class RequestSentAlreadyError(BadRequestError):
    """Raised when the user tries to send a friend request to the same user again."""
    pass


class AlreadyFriendsError(BadRequestError):
    """Raised when the user tries to send a friend request to the same user again."""
    pass
