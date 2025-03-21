# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import auth, users, messages
from config import HOST, PORT

# Se crean las tablas a partir de los modelos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chimeo API")

# Configuracion de CORS (solo para probar en web)
# app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],  # In production, replace with specific origins
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
# )

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(messages.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Chimeo API",
        "version": "1.0.0"
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True
    )
