from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Convert async URL to sync URL for batch scripts
# sqlite+aiosqlite:///... -> sqlite:///...
sync_database_url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")

engine = create_engine(
    sync_database_url,
    echo=False, # verbose setting off for training script
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

def get_db_sync():
    """Synchronous DB session generator"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
