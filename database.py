from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

# El engine es el objeto a partir del cual se interactua con la base de datos.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Devuelve una clase, no una instancia. Las transacciones no se realizan hasta que se llama a commit(). Se usara esta clase para crear sesiones con la base de datos.
SessionLocal = sessionmaker(autoflush=False, bind=engine)

# Devuelve una clase, no una instancia. Define la estructura global de las tablas (modelos) de la base de datos. Todos los modelos deben heredar de esta clase.
Base = declarative_base()

# Es un generador que se encarga de abrir y cerrar conexiones con la base de datos


def get_db():
    db = SessionLocal()  # Instancia de clase de arriba
    try:
        yield db
    finally:
        # Cierra la conexion con la base de datos, aunque salten excepciones
        # La conexion se cierra una vez se ha respondido a la peticion
        db.close()
