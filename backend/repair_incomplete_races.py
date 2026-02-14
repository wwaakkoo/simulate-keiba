import asyncio
import logging
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from sqlalchemy import select, func
from app.core.database import async_session
from app.models import Race, RaceEntry
from app.scraper.service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting repair process...")
    async with async_session() as session:
        # Find incomplete races (less than 5 entries)
        logger.info("Scanning for incomplete races...")
        
        # Subquery to count entries per race
        stmt = (
            select(Race.race_id, func.count(RaceEntry.id).label("entry_count"))
            .join(RaceEntry, Race.id == RaceEntry.race_id, isouter=True)
            .group_by(Race.race_id, Race.id)
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        target_race_ids = []
        for r in rows:
            if r.entry_count < 5:
                target_race_ids.append(r.race_id)
                
        if not target_race_ids:
            logger.info("No incomplete races found.")
            return

        logger.info(f"Found {len(target_race_ids)} incomplete races (entries < 5).")
        
        service = ScraperService(session)
        
        for i, race_id in enumerate(target_race_ids):
            logger.info(f"Repairing {i+1}/{len(target_race_ids)}: {race_id}")
            
            try:
                # 1. Delete existing race data
                race_stmt = select(Race).where(Race.race_id == race_id)
                race_row = await session.execute(race_stmt)
                race_obj = race_row.scalar_one_or_none()
                
                if race_obj:
                    await session.delete(race_obj)
                    await session.flush()
                
                # 2. Re-scrape
                # ScraperService.scrape_race will commit
                await service.scrape_race(race_id)
                
                # Cool down
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to repair race {race_id}: {e}")
        
        await service.close()
        logger.info("Repair process completed.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
