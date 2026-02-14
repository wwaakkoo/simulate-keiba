import asyncio
import logging
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from sqlalchemy import select, func
from app.core.database import async_session
from app.models import Race, RaceEntry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    async with async_session() as session:
        # Race count
        result = await session.execute(select(func.count(Race.id)))
        total_races = result.scalar()
        
        # Entry count
        result = await session.execute(select(func.count(RaceEntry.id)))
        total_entries = result.scalar()
        
        avg_entries = total_entries / total_races if total_races > 0 else 0
        
        # Incomplete races
        stmt = (
            select(Race.race_id, func.count(RaceEntry.id).label("entry_count"))
            .join(RaceEntry, Race.id == RaceEntry.race_id, isouter=True)
            .group_by(Race.race_id, Race.id)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        incomplete_count = 0
        for r in rows:
            if r.entry_count < 5:
                incomplete_count += 1
        
        print("\n--- Data Quality Report ---")
        print(f"Total Races: {total_races}")
        print(f"Total Entries: {total_entries}")
        print(f"Avg Entries/Race: {avg_entries:.2f}")
        print(f"Incomplete Races (< 5 entries): {incomplete_count}")
        print("---------------------------\n")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
