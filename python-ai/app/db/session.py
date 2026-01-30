import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

def get_engine():
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "sentinelstream")
    db_user = os.getenv("POSTGRES_USER", "sentinel")
    db_password = os.getenv("POSTGRES_PASSWORD", "sentinel_pass_2026")
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(database_url, pool_pre_ping=True, echo=False)
    return engine


def get_session() -> Session:
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()
