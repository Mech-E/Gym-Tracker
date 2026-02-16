from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATASAE_URL = "sqlite:///./gymtracker.db"

engine = create_engine( 
    DATASAE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()