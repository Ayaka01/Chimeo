import logging
import uvicorn
from fastapi.responses import HTMLResponse

from config import configure_logging, HOST, PORT, DEBUG, LANDING_PAGE_HTML

if __name__ == "__main__":
    configure_logging(level=logging.DEBUG if DEBUG else logging.INFO)
    logger = logging.getLogger(__name__)

    from app import app, init_database
    @app.get("/", response_class=HTMLResponse)
    async def root():
        logger.info("Root endpoint accessed")
        return HTMLResponse(content=LANDING_PAGE_HTML)

    logger.info("Starting Chimeo API")
    init_database()

    logger.info(f"Starting server on {HOST}:{PORT}")
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
