"""
Custom exceptions for the Chimeo application.

This module defines custom exception classes that can be
raised throughout the application.
"""
from typing import Dict, Any, Optional, List

class APIError(Exception):
    """Base exception class for API errors."""
    
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
        
        
class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self, 
        entity: str, 
        identifier: str,
        error_code: str = "RESOURCE_NOT_FOUND"
    ):
        detail = f"{entity} not found: {identifier}"
        super().__init__(
            status_code=404,
            detail=detail,
            error_code=error_code
        )
        
        
class AuthenticationError(APIError):
    """Raised when authentication fails."""
    
    def __init__(
        self, 
        detail: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR"
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code=error_code
        )
        
        
class AuthorizationError(APIError):
    """Raised when a user is not authorized to perform an action."""
    
    def __init__(
        self, 
        detail: str = "Not authorized",
        error_code: str = "AUTHORIZATION_ERROR"
    ):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code=error_code
        )
        
        
class ValidationError(APIError):
    """Raised when input validation fails."""
    
    def __init__(
        self, 
        detail: str = "Validation error",
        errors: Optional[List[Dict[str, Any]]] = None,
        error_code: str = "VALIDATION_ERROR"
    ):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code=error_code,
            errors=errors
        )
        
        
class DatabaseError(APIError):
    """Raised when a database operation fails."""
    
    def __init__(
        self, 
        detail: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR"
    ):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code=error_code
        ) 