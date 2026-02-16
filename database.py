import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATASAE_URL = os.getenv("DATABASE_URL", "sqlite:///./gymtracker.db")

if DATASAE_URL.startswith("postgres://"):
    DATASAE_URL = DATASAE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATASAE_URL.startswith("sqlite") else {}

engine = create_engine( DATASAE_URL,connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()