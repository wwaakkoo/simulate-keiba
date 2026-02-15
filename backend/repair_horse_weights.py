import asyncio
import sys
import os
from sqlalchemy import select, update, or_
from app.core.database import async_session
from app.models.race_entry import RaceEntry

# Add backend to path
sys.path.append(os.getcwd())

async def repair_horse_weights():
    async with async_session() as session:
        # Find entries with suspicious horse_weight (e.g., < 100kg, which implies it's a time or other value)
        # Assuming typical horse weight is 400-600kg. 
        # Values like 33.7 are definitely last_3f.
        result = await session.execute(
            select(RaceEntry).where(
                or_(
                    RaceEntry.horse_weight < 100,
                    RaceEntry.horse_weight == None # Just to check coverage, but we filter < 100
                )
            )
        )
        entries = result.scalars().all()
        
        count = 0
        for entry in entries:
            if entry.horse_weight is not None and entry.horse_weight < 200:
                print(f"Repairing Entry ID {entry.id}: Weight {entry.horse_weight} -> Last3F")
                
                # Move to last_3f if it's currently None
                if entry.last_3f is None:
                    entry.last_3f = float(entry.horse_weight)
                
                # Clear horse_weight
                entry.horse_weight = None
                entry.horse_weight_diff = None # Also clear diff if it was derived from the same cell
                count += 1
        
        if count > 0:
            await session.commit()
            print(f"Successfully repaired {count} entries.")
        else:
            print("No suspicious entries found.")

if __name__ == "__main__":
    asyncio.run(repair_horse_weights())
