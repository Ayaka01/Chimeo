from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from database import Base

# Hereda de la clase generada por declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    display_name = Column(String, index=True)
    # NO tendremos usuarios con el mismo email
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
