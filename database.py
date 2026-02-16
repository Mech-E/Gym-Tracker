# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_RENDER")  # optional fallback

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it in Render dashboard (Environment) "
        "or provide it via .env locally."
    )

# Render/Heroku sometimes use postgres:// which should be postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
# Only sqlite needs connect_args
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
