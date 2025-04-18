
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
        
