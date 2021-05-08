from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base

engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

Base.metadata.create_all(engine)
