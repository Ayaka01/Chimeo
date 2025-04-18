import logging
from typing import Dict, Any
from fastapi.exceptions import RequestValidationError


logger = logging.getLogger(__name__)


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

