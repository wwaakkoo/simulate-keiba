
import asyncio
import logging
import sys
import os
from datetime import date, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.scraper.service import ScraperService
from app.predictor.sync_database import SessionLocal # Using sync session for engine, but ScraperService needs AsyncSession?
# service.py uses AsyncSession.
# database.py likely has async_session factory.
# Let's check database.py or create a quick async engine setup if needed.
# Actually, let's check how main.py injects session.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup (Async)
# Assuming keiba.db is in data/
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR)) # repo root
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def main():
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)
    
    current_date = start_date
    
    async with AsyncSessionLocal() as session:
        service = ScraperService(session)
        
        try:
            while current_date <= end_date:
                # Only scrape weekends? Or every day to be safe?
                # JRA races are mostly Sat/Sun, but sometimes Mon/Hol.
                # NAR (Local) might be everyday, but user might target JRA.
                # Netkeiba lists all.
                # Let's check if user wants JRA only or all.
                # Defaulting to checking all days but being fast if no list.
                
                date_str = current_date.strftime("%Y%m%d")
                
                # Retrieve race list
                # service.scrape_date handles everything.
                
                try:
                    result = await service.scrape_date(date_str)
                    if result['total'] > 0:
                        logger.info(f"Summary for {date_str}: {result}")
                    else:
                        # logger.info(f"No races for {date_str}")
                        pass
                except Exception as e:
                    logger.error(f"Failed to scrape {date_str}: {e}")
                
                current_date += timedelta(days=1)
                await asyncio.sleep(1) # Politeness
                
        finally:
            await service.close()

if __name__ == "__main__":
    # Windows SelectorEventLoop policy fix for Python 3.8+ if needed (usually fine in 3.11+)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
