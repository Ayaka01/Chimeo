import logging
import uvicorn
from fastapi.responses import HTMLResponse

from src.config import configure_logging, HOST, PORT, DEBUG, LANDING_PAGE_HTML

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
