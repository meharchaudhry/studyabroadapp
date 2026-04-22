from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

db_url = settings.SQLALCHEMY_DATABASE_URI

# Supabase Transaction Pooler (port 6543) does not support prepared statements
# pool_pre_ping ensures stale connections are automatically recycled
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
else:
    connect_args = {}
    if "pooler.supabase.com" in db_url:
        # Disable prepared statements for PgBouncer transaction mode
        connect_args["options"] = "-c statement_timeout=30000"
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,       # Recycle dead connections automatically
        pool_size=5,              # Keep 5 persistent connections
        max_overflow=10,          # Allow 10 extra under load
        pool_recycle=300,         # Recycle connections every 5 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

