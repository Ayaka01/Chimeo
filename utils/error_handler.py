"""
Error handling utilities for the Chimeo application.

This module provides standardized error handling 
and response formatting for the API.
"""
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
from fastapi import status
from pydantic import ValidationError as PydanticValidationError
from fastapi.exceptions import RequestValidationError

from .exceptions import (
    APIError, ResourceNotFoundError, AuthenticationError, 
    AuthorizationError, ValidationError, DatabaseError
)

logger = logging.getLogger(__name__)


def format_error_response(
    detail: str, 
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    errors: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Format a standardized error response.
    
    Args:
        detail: The error message
        status_code: HTTP status code
        error_code: Machine-readable error code
        errors: Detailed error information for validation errors
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "detail": detail,
        "status_code": status_code,
    }
    
    if error_code:
        response["error_code"] = error_code
        
    if errors:
        response["errors"] = errors
        
    return response


def handle_validation_error(exc: RequestValidationError) -> Dict[str, Any]:
    error_details = []
    for error in exc.errors():
        error_details.append(
            {
                "location": ".".join(map(str, error["loc"])),
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return {"detail": "Validation Error", "errors": error_details}


def database_error_handler(func: Callable) -> Callable:
    """
    Decorator to handle database errors.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise DatabaseError()
    return wrapper


# Common error handlers
def handle_not_found(entity: str, identifier: str) -> None:
    """
    Handle not found errors consistently.
    
    Args:
        entity: Type of entity (e.g., "User", "Message")
        identifier: Identifier that wasn't found
        
    Raises:
        ResourceNotFoundError: with appropriate entity and identifier
    """
    logger.warning(f"{entity} not found: {identifier}")
    raise ResourceNotFoundError(entity=entity, identifier=identifier)


def handle_unauthorized(reason: str = "Not authenticated") -> None:
    """
    Handle unauthorized access consistently.
    
    Args:
        reason: Reason for unauthorized access
        
    Raises:
        AuthenticationError: with appropriate message
    """
    logger.warning(f"Unauthorized access: {reason}")
    raise AuthenticationError(detail=reason)


def handle_forbidden(reason: str = "Access forbidden") -> None:
    """
    Handle forbidden access consistently.
    
    Args:
        reason: Reason for forbidden access
        
    Raises:
        AuthorizationError: with appropriate message
    """
    logger.warning(f"Forbidden access: {reason}")
    raise AuthorizationError(detail=reason) 