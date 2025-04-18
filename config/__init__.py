from config.settings import (
    DATABASE_URL,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    HOST,
    PORT,
    CORS_ENABLED,
    CORS_ORIGINS,
    CORS_METHODS,
    CORS_HEADERS,
    WS_HEARTBEAT_INTERVAL,
    DEBUG
)

from config.logging import configure_logging
from config.templates import (
    LANDING_PAGE_HTML,
    API_DESCRIPTION,
    AUTH_ENDPOINTS_HTML,
    USERS_ENDPOINTS_HTML,
    MESSAGES_ENDPOINTS_HTML
) 