# Chimeo API

## Description

This API provides endpoints for user authentication, messaging, and friend management for the Chimeo messaging application.

## Features

*   User registration and authentication (JWT-based)
*   Friend requests and friend management
*   Real-time messaging with WebSockets
*   Message delivery status tracking

## Technologies Used

*   **Backend Framework**: FastAPI
*   **Database**: SQLAlchemy (defaulting to SQLite, configurable via `DATABASE_URL`)
*   **Data Validation**: Pydantic
*   **Asynchronous Server Gateway Interface (ASGI)**: Uvicorn
*   **Authentication**: JWT with Passlib for password hashing
*   **WebSockets**: For real-time communication
*   **Configuration**: `python-dotenv`
*   **API Documentation**: Swagger UI, ReDoc, MkDocs (for static documentation)

## Project Structure

```
chimeo_server/
├── .env.example        # Example environment variables
├── requirements.txt    # Project dependencies
├── src/                # Source code
│   ├── app.py          # FastAPI application setup, middleware, exception handlers
│   ├── main.py         # Application entry point (runs Uvicorn)
│   ├── database.py     # SQLAlchemy setup (engine, Base)
│   ├── config/         # Configuration files
│   │   ├── __init__.py
│   │   ├── settings.py # Loads environment variables, defines app settings
│   │   ├── logging.py  # Logging configuration
│   │   └── templates.py# API description and HTML templates for landing/doc pages
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic schemas for data validation
│   ├── routes/         # API endpoint definitions (auth, users, messages)
│   ├── services/       # Business logic
│   └── utils/          # Utility functions and custom exceptions
└── ...                 # Other project files (.gitignore, etc.)
```

## Configuration

The application uses a `.env` file to manage environment variables. Create a `.env` file in the project root by copying `.env.example` (if one exists, otherwise create it manually).

Key environment variables:

*   `DATABASE_URL`: The connection string for your database (e.g., `sqlite:///./chimeo.db` or `postgresql://user:password@host:port/database`).
*   `SECRET_KEY`: A secret key for JWT token generation. Generate a strong random key.
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Lifetime of access tokens (default: 30).
*   `REFRESH_TOKEN_EXPIRE_DAYS`: Lifetime of refresh tokens (default: 7).
*   `HOST`: Host address for the server (default: `0.0.0.0`).
*   `PORT`: Port for the server (default: `8000`).
*   `DEBUG`: Set to `true` for debug mode (enables auto-reload and more verbose logging) (default: `false`).

Example `.env` file:
```env
DATABASE_URL="sqlite:///./chimeo.db"
SECRET_KEY="your_strong_secret_key_here"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
HOST="0.0.0.0"
PORT=8000
DEBUG=true
```

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd chimeo_server
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the `.env` file:**
    Create a `.env` file in the project root as described in the "Configuration" section.

5.  **Initialize the database:**
    The database tables are created automatically when the application starts (via `Base.metadata.create_all(bind=engine)` in `src/app.py`).

6.  **Run the application:**
    ```bash
    python src/main.py
    ```
    The API will be available at `http://<HOST>:<PORT>` (e.g., `http://0.0.0.0:8000` or `http://localhost:8000`).

## API Documentation

Once the server is running, you can access the API documentation at:

*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`
*   **Landing Page**: `http://localhost:8000/` (provides links to endpoint-specific HTML documentation)

### Authentication
Most endpoints require authentication using a JWT bearer token. Obtain your token by registering a new account (`/auth/register`) or logging in (`/auth/login`). Include the token in the `Authorization` header:
```
Authorization: Bearer your_token_here
```
