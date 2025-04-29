import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.responses import HTMLResponse

from src.database import engine, Base
from src.routes import users, messages, auth
from src.config import CORS_ENABLED, CORS_ORIGINS, CORS_METHODS, CORS_HEADERS, API_DESCRIPTION, configure_logging, \
    DEBUG, LANDING_PAGE_HTML, HOST, PORT
from src.utils.error_handler import handle_validation_error
from src.utils.exceptions import APIError

def create_application() -> FastAPI:
    app = FastAPI(
        title="Chimeo API",
        description=API_DESCRIPTION,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "authentication",
                "description": "Operations for user registration, login, and token management"
            },
            {
                "name": "users",
                "description": "Operations related to user profiles and friend management"
            },
            {
                "name": "messages",
                "description": "Operations for sending and receiving messages"
            }
        ],
    )

    if CORS_ENABLED:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=CORS_METHODS,
            allow_headers=CORS_HEADERS,
        )
        logger.info(f"CORS enabled with origins: {CORS_ORIGINS}")
    else:
        logger.info("CORS disabled")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        client_host = request.client.host if request.client else "unknown"
        request_path = request.url.path
        request_method = request.method

        logger.info(f"Request started: {request_method} {request_path} from {client_host}")

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(f"Request completed: {request_method} {request_path} - {response.status_code} ({process_time:.2f}ms)")

        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content=handle_validation_error(exc),
        )

    @app.exception_handler(APIError)
    async def api_error_handler(_: Request, exc: APIError):
        logger.warning(f"API error: {exc.detail} (code: {exc.error_code})")
        content = {
            "detail": exc.detail,
            "status_code": exc.status_code
        }

        if exc.error_code:
            content["error_code"] = exc.error_code

        if exc.errors:
            content["errors"] = exc.errors

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(messages.router)

    return app


def init_database():
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)

configure_logging(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)
app = create_application()
@app.get("/", response_class=HTMLResponse)
async def root():
    logger.info("Root endpoint accessed")
    return HTMLResponse(content=LANDING_PAGE_HTML)

logger.info("Starting Chimeo API")
init_database()

logger.info(f"Starting server on {HOST}:{PORT}")

